# core/trader_engine.py
from gm.api import (
    get_position,
    order_target_percent,
    order_volume,  # 【新增】导入按数量下单API
    current,  # 【新增】导入实时行情API
    OrderSide_Buy,  # 【新增】买入方向常量
    OrderSide_Sell,  # 【新增】卖出方向常量
    OrderType_Market,  # 【新增】市价单类型
    OrderType_Limit,  # 【新增】限价单类型
    PositionEffect_Open,  # 【新增】开仓效果常量
    PositionEffect_Close,  # 【新增】平仓效果常量
    get_cash,  # 【修复】使用 get_cash 而非 get_account（适配当前SDK版本）
)
from config import settings


class Position:
    """统一的持仓对象（包含成本价字段）"""
    def __init__(
        self,
        stock_code,
        volume,
        side=None,
        open_price=0.0,
        cost_price=0.0,
        avg_price=0.0,
        last_price=0.0,
        fpnl=0.0,
        market_value=0.0,
        raw=None
    ):
        self.stock_code = stock_code
        self.volume = volume
        self.side = side

        # 三个成本价字段全部写入真实成本价
        self.open_price = open_price
        self.cost_price = cost_price
        self.avg_price = avg_price

        self.last_price = last_price
        self.fpnl = fpnl
        self.market_value = market_value

        # 保存掘金原始持仓，便于调试
        self.raw = raw
        
        # ⭐⭐⭐ T+1合规核心字段：当前可卖数量（止损/止盈必须用此字段）
        # 根据掘金SDK v3.0.183实测：
        # - available: 总可平数量（含今日买入，❌不可用于卖出）
        # - available_now: 当前可卖数量（✅止损/止盈必须用此字段）
        # - available_today: 今日买入数量（仅用于调试）
        if raw:
            self.available_now = raw.get("available_now", 0)  # ✅ 当前可卖数量
            self.available_today = raw.get("available_today", 0)  # 今日买入数量
            self.volume_today = raw.get("volume_today", 0)  # 今日成交量
            
            # can_use_volume 作为兼容字段，映射到 available_now
            self.can_use_volume = self.available_now
        else:
            self.available_now = 0
            self.available_today = 0
            self.volume_today = 0
            self.can_use_volume = 0


class TraderEngine:
    """交易引擎（兼容 gm 3.0.183，无 tick API）"""

    def __init__(self, context):
        self.context = context
        self.account_id = settings.ACCOUNT_ID

    # ----------------------------------------------------------------------
    # 1) 持仓查询（核心：成本价映射）
    # ----------------------------------------------------------------------
    def query_positions(self):
        raw_positions = get_position(account_id=self.account_id)
        positions = []

        for p in raw_positions:
            # 掘金真实成本价字段
            vwap_open = p.get("vwap_open", 0.0)
            vwap = p.get("vwap", 0.0)
            cost = p.get("cost", 0.0)
            volume = p.get("volume", 0)

            # 计算最终成本价
            cost_price = 0.0
            if vwap_open and vwap_open > 0:
                cost_price = vwap_open
            elif vwap and vwap > 0:
                cost_price = vwap
            elif cost > 0 and volume > 0:
                cost_price = cost / volume

            # 三个字段全部写入成本价
            open_price = cost_price
            avg_price = cost_price

            pos = Position(
                stock_code=p["symbol"],
                volume=volume,
                side=p.get("side", None),
                open_price=open_price,
                cost_price=cost_price,
                avg_price=avg_price,
                last_price=p.get("last_price", 0.0),  # ✔ 用 last_price 替代 tick
                fpnl=p.get("fpnl", 0.0),
                market_value=p.get("market_value", 0.0),
                raw=p,
            )

            positions.append(pos)

        return positions

    # ----------------------------------------------------------------------
    # 2) 资产查询（账户资金信息）
    # ----------------------------------------------------------------------
    def query_asset(self):
        """
        查询账户资产信息（适配当前SDK版本）
        
        返回:
            dict: 包含 cash, total_asset, market_value 等字段
        """
        try:
            # 【修复】使用 get_cash() 获取账户资金信息
            cash_info = get_cash()
            
            # 【关键修复】正确理解掘金SDK字段含义
            # - nav: Net Asset Value = 总资产（不是可用资金！）
            # - 可用资金 = 总资产 - 持仓市值
            
            # 1. 获取总资产
            total_asset = 0.0
            if hasattr(cash_info, 'nav'):
                total_asset = cash_info.nav  # ✅ nav 是总资产
            elif hasattr(cash_info, 'total_asset'):
                total_asset = cash_info.total_asset
            elif hasattr(cash_info, 'cash_balance'):
                total_asset = cash_info.cash_balance
            
            # 2. 查询持仓市值
            positions = self.query_positions()
            market_value = sum(pos.market_value for pos in positions) if positions else 0
            
            # 3. 计算可用资金 = 总资产 - 持仓市值
            available_cash = total_asset - market_value
            
            # 4. 冻结资金
            frozen_cash = 0.0
            if hasattr(cash_info, 'frozen_cash'):
                frozen_cash = cash_info.frozen_cash
            elif hasattr(cash_info, 'order_frozen'):
                frozen_cash = cash_info.order_frozen
            
            # 5. 组装返回数据
            asset_info = {
                'cash': available_cash,           # 可用资金 = 总资产 - 持仓市值
                'total_asset': total_asset,       # 总资产（来自 nav）
                'market_value': market_value,     # 持仓市值
                'frozen_cash': frozen_cash,       # 冻结资金
            }
            
            return asset_info
        
        except Exception as e:
            print(f"[TraderEngine] 查询资产失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    # ----------------------------------------------------------------------
    # 3) 获取最新价（使用 current() 实时行情 API - gm 3.0.183 正确用法）
    # ----------------------------------------------------------------------
    def get_latest_prices(self, symbols):
        """
        获取最新价（gm 3.0.183 正确用法）
        symbols: ['SZSE.300048', 'SHSE.603920']
        返回: {symbol: latest_price}
        
        ⚠️ 重要：gm 3.0.183 的 current() 返回的是 list 而不是 DataFrame！
        - 只支持 symbols 和 fields 两个参数
        - 不支持 frequency、count 等参数
        - fields='price' 返回最新成交价
        - 返回值类型：list of dict
        - ⚠️ 单股票查询时，返回的dict可能不包含'symbol'字段！
        """
        result = {}

        try:
            data = current(
                symbols=symbols,      # ✔ 必须是 symbols（复数）
                fields='price'        # ✔ gm 3.0.183 支持的字段：price（最新价）
            )
        except Exception as e:
            print(f"[TraderEngine] current() 调用失败: {e}")
            return {sym: None for sym in symbols}

        # ⚠️ gm 3.0.183 返回的是 list，不是 DataFrame！
        # 数据格式（多股票）：[{'symbol': 'SZSE.300048', 'price': 7.06}, ...]
        # 数据格式（单股票）：[{'price': 35.88}]  ← 没有 symbol 字段！
        if data is None or len(data) == 0:
            return {sym: None for sym in symbols}

        # 遍历 list，提取价格
        # 策略：如果返回数量与请求数量一致，按顺序匹配
        if len(data) == len(symbols):
            # 情况1：返回数量匹配，按顺序对应
            for i, item in enumerate(data):
                sym = symbols[i]
                price = float(item['price'])
                result[sym] = price
        else:
            # 情况2：尝试从 item 中获取 symbol 字段
            for item in data:
                if 'symbol' in item:
                    sym = item['symbol']
                    price = float(item['price'])
                    result[sym] = price
                else:
                    # 无法确定是哪个股票，跳过
                    print(f"[TraderEngine] 警告：返回数据缺少 symbol 字段，无法匹配")

        # 对于没有返回的 symbol 补 None
        for sym in symbols:
            if sym not in result:
                result[sym] = None

        return result

    # ----------------------------------------------------------------------
    # 4) 下单接口：按股数买卖（止损模块需要）
    # ----------------------------------------------------------------------
    def order_stock(self, symbol, side, volume, price=None, reason=""):
        """
        按指定数量下单（支持买入和卖出）
        
        参数:
            symbol: 股票代码，如 'SHSE.600821'
            side: 买卖方向，"BUY" 或 "SELL"
            volume: 交易数量（股）
            price: 限价价格（None 表示市价单）
            reason: 下单原因（用于日志）
        
        返回:
            order_id 或 None
        """
        try:
            from gm.api import OrderSide_Buy, OrderSide_Sell, OrderType_Market, OrderType_Limit, PositionEffect_Open, PositionEffect_Close
            
            # 转换方向
            if side.upper() == "BUY":
                order_side = OrderSide_Buy
                position_effect = PositionEffect_Open
            elif side.upper() == "SELL":
                order_side = OrderSide_Sell
                position_effect = PositionEffect_Close
            else:
                print(f"[TraderEngine] 无效的买卖方向: {side}")
                return None
            
            # 确定订单类型
            if price and price > 0:
                order_type = OrderType_Limit
                order_price = price
            else:
                order_type = OrderType_Market
                order_price = 0.0
            
            # 调用掘金API下单
            order_id = order_volume(
                symbol=symbol,
                volume=volume,
                side=order_side,
                order_type=order_type,
                price=order_price,
                position_effect=position_effect
            )
            
            print(f"[TraderEngine] 下单成功: {symbol} {side} {volume}股 @ {order_price if order_price > 0 else '市价'} (原因: {reason})")
            return order_id
        
        except Exception as e:
            print(f"[TraderEngine] 下单失败 {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return None
