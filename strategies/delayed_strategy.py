# -*- coding: utf-8 -*-
"""
延时策略 - 掘金量化版
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

版本说明: V9.0 - 基于掘金平台
"""
import os
import json
import datetime
from utils.logger import get_logger
from config import settings


class DelayedStrategy:
    def __init__(self, engine):
        self.engine = engine
        
        # 路径配置
        self.personalities_file = os.path.join(settings.DATA_DIR, "stock_personalities.json")
        self.watchlist_file = os.path.join(settings.DATA_DIR, "delayed_watchlist.json")
        
        # 加载配置
        self.stock_personalities = self._load_personalities()
        self.delayed_watchlist = self._load_watchlist()

    def _load_personalities(self):
        logger = get_logger()
        if not os.path.exists(self.personalities_file):
            if logger:
                logger.log(f"[错误] 配置文件不存在: {self.personalities_file}")
            return {}
        try:
            with open(self.personalities_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if logger:
                logger.log(f"[成功] 加载股票个性配置: {len(data)}只股票")
                # 【调试】输出600821的配置
                if '600821' in data:
                    logger.log(f"[调试] 600821配置: type={data['600821'].get('type')}")
                else:
                    logger.log(f"[警告] 配置文件中未找到600821")
            return data
        except Exception as e:
            if logger:
                logger.log(f"[错误] 读取配置文件失败: {e}")
            return {}

    def _load_watchlist(self):
        logger = get_logger()
        if not os.path.exists(self.watchlist_file):
            empty_list = {"last_update": "", "watchlist": {}}
            self._save_watchlist(empty_list)
            return empty_list
        try:
            with open(self.watchlist_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            if logger:
                logger.log(f"[警告] 加载观察名单失败: {e}")
            return {"last_update": "", "watchlist": {}}

    def _save_watchlist(self, data=None):
        logger = get_logger()
        if data is None:
            data = self.delayed_watchlist
            
        data['last_update'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            with open(self.watchlist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            if logger:
                logger.log(f"[保存] 观察名单已更新: {len(data.get('watchlist', {}))}只")
        except Exception as e:
            if logger:
                logger.log(f"[错误] 保存观察名单失败: {e}")

    # ============================================================
    # ⭐ 工业级辅助方法：判断股票类型和观察名单状态
    # ============================================================
    def is_delayed_stock(self, code):
        """
        判断股票是否为延时类型
        
        参数:
            code: 股票代码 (支持 SHSE.600821 或 600821 格式)
        
        返回:
            True: 是延时股票
            False: 非延时股票
        """
        # 提取纯数字代码用于配置查找
        pure_code = code.split('.')[-1] if '.' in code else code
        
        # 获取配置（优先使用纯数字代码匹配）
        config = self.stock_personalities.get(pure_code, 
                   self.stock_personalities.get(code, 
                   self.stock_personalities.get('default', {})))
        
        stock_type = config.get('type', 'immediate')
        return stock_type == 'delayed'

    def in_watchlist(self, code):
        """
        判断股票是否在延时观察名单中
        
        参数:
            code: 股票代码 (必须与watchlist中的key一致,如 SHSE.600821)
        
        返回:
            True: 在观察名单中
            False: 不在观察名单中
        """
        return code in self.delayed_watchlist.get('watchlist', {})

    def _get_latest_volume_ratio(self, code):
        """
        从 signals 目录读取指定股票的最新信号文件，获取当前量比
        
        参数:
            code: 股票代码 (如 SHSE.600722 或 SZSE.300444)
        
        返回:
            float: 最新量比值，如果未找到则返回 None
        """
        import glob
        
        try:
            # 【股票代码标准化】提取纯数字代码
            # 支持格式：SHSE.600722 -> 600722, SZSE.300444 -> 300444
            pure_code = code.split('.')[-1] if '.' in code else code
            
            # 查找 signals 目录下所有未处理的信号文件
            signal_files = glob.glob(os.path.join(settings.SIGNAL_DIR_INPUT, "*.txt"))
            
            latest_time = None
            latest_vr = None
            
            for sig_file in signal_files:
                try:
                    with open(sig_file, 'r', encoding='utf-8') as f:
                        lines = f.read().strip().split('\n')
                    
                    for line in lines:
                        if not line.strip():
                            continue
                        
                        try:
                            sig_data = json.loads(line)
                            sig_code = sig_data.get('code', '')
                            
                            # 【关键修复】标准化信号文件中的股票代码
                            # 支持格式：
                            # - 300444.SZ -> 300444
                            # - 603353.SH -> 603353
                            # - SZSE.300444 -> 300444
                            # - SHSE.603353 -> 603353
                            if '.' in sig_code:
                                parts = sig_code.split('.')
                                # 判断哪部分是数字代码
                                if parts[0].isdigit():
                                    # 格式：300444.SZ
                                    sig_pure = parts[0]
                                elif parts[1].isdigit():
                                    # 格式：SZSE.300444
                                    sig_pure = parts[1]
                                else:
                                    # 都不是数字，跳过
                                    continue
                            else:
                                sig_pure = sig_code
                            
                            # 匹配纯数字代码
                            if sig_pure == pure_code:
                                # 提取文件修改时间
                                file_mtime = os.path.getmtime(sig_file)
                                
                                # 保留最新的信号
                                if latest_time is None or file_mtime > latest_time:
                                    latest_time = file_mtime
                                    latest_vr = float(sig_data.get('volume_ratio', 0))
                        except:
                            continue
                except:
                    continue
            
            return latest_vr
            
        except Exception as e:
            logger = get_logger()
            if logger:
                logger.log(f"[警告] 读取量比失败 {code}: {e}")
            return None

    def process_signal(self, code, action, price, volume_ratio):
        """
        处理信号，判断是否加入延时观察名单
        
        注意：只处理 BUY 信号，SELL 直接返回 False
        """
        logger = get_logger()
        
        if action != "BUY":
            return False
        
        # 【修复】提取纯数字代码用于配置查找
        # 支持格式：SHSE.600821 -> 600821, SZSE.300641 -> 300641
        pure_code = code.split('.')[-1] if '.' in code else code
        
        # 获取配置（优先使用纯数字代码匹配）
        config = self.stock_personalities.get(pure_code, 
                   self.stock_personalities.get(code, 
                   self.stock_personalities.get('default', {})))
        stock_type = config.get('type', 'immediate')
        
        # 【新增】输出配置信息
        if logger:
            logger.log(f"[延时策略-检查] {code} (纯代码:{pure_code}) | 类型: {stock_type} | 量比: {volume_ratio:.2f}")
        
        if stock_type != 'delayed':
            if logger:
                logger.log(f"[延时策略-跳过] {code} 类型为 {stock_type}，非延时股票")
            return False

        # 量比过滤
        min_vr = config.get('min_volume_ratio', 18.0)
        if volume_ratio < min_vr:
            if logger:
                logger.log(f"[延时策略-跳过] {code} 量比 {volume_ratio:.2f} < 阈值 {min_vr:.2f}")
            return False
        
        # 检查是否已在观察名单中
        today = datetime.date.today()
        if code in self.delayed_watchlist.get('watchlist', {}):
            existing_item = self.delayed_watchlist['watchlist'][code]
            existing_target_date_str = existing_item.get('target_date', '')
            
            if existing_target_date_str:
                existing_target_date = datetime.datetime.strptime(existing_target_date_str, '%Y-%m-%d').date()
                
                if today >= existing_target_date:
                    if logger:
                        logger.log(f"[延时策略] {code} 已在名单中且今天是目标日，拒绝重复加入")
                    return False
                
                if logger:
                    logger.log(f"[延时策略] {code} 已在名单中，跳过")
                return False
            
        # 加入名单
        signal_date = datetime.date.today()
        delay_days = max(0, int(config.get('delay_days', 1)))
        target_date = self._calculate_target_date(signal_date, delay_days)
        
        watchlist_item = {
            'name': config.get('name', code),
            'action': 'BUY',
            'signal_date': signal_date.strftime('%Y-%m-%d'),
            'target_date': target_date.strftime('%Y-%m-%d'),
            'trigger_price': price,
            'trigger_volume_ratio': volume_ratio,
            'status': 'waiting',
            'delay_days': delay_days
        }
        
        self.delayed_watchlist['watchlist'][code] = watchlist_item
        self._save_watchlist()
        
        if logger:
            logger.log(f"[延时策略] {code} 已加入观察名单，目标日: {target_date}")
        return True

    def _calculate_target_date(self, signal_date, delay_days):
        """计算目标日期（跳过周末）"""
        target = signal_date
        remaining = delay_days
        safety_counter = 0
        
        while remaining > 0 and safety_counter < 50:
            target += datetime.timedelta(days=1)
            if target.weekday() < 5:  # 跳过周末
                remaining -= 1
            safety_counter += 1
            
        return target

    def check_and_execute(self):
        """
        检查观察名单,判断是否到达目标日期并执行买入
        
        ⭐ 工业级延时策略核心逻辑(三阶段控制):
        
        ① target_date 之前 → 禁止买入(无论量比多少)
        ② target_date 当天 → 两种情况:
           - 情况A: 盘中量比 ≥ trigger_volume_ratio → 立即提前买入 → 删除watchlist
           - 情况B: 盘中量比始终 < trigger_volume_ratio → 14:39保底买入 → 删除watchlist
        ③ target_date 之后 → 延时策略过期 → 自动删除watchlist(不再买入)
        
        执行逻辑:
        - 路径 A(信号优先): 量比达到门槛 → 立即买入
        - 路径 B(保底机制): 14:39 之后 → 强制买入
        """
        logger = get_logger()
        watchlist = self.delayed_watchlist.get('watchlist', {})
        
        # 【新增】每次调用都输出日志,方便调试
        if logger:
            if not watchlist:
                logger.log(f"📋 [延时策略] 观察名单为空,跳过检查")
            else:
                logger.log(f"📋 [延时策略] 检查 {len(watchlist)} 只股票的观察名单...")
        
        if not watchlist:
            return
            
        today = datetime.date.today()
        now_time = datetime.datetime.now().strftime("%H%M")
        codes_to_remove = []
        
        # 【关键修复】使用 list() 创建副本，避免遍历时修改字典导致 RuntimeError
        for code, item in list(watchlist.items()):
            try:
                target_date_str = item.get('target_date', '')
                if not target_date_str:
                    continue
                    
                target_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d').date()
                
                # ==================== ① target_date 之前: 禁止买入 ====================
                if today < target_date:
                    if logger:
                        logger.log(f"[延时策略-未到目标日] {code} 目标日={target_date}, 今天={today}, 禁止买入")
                    continue
                
                # ==================== ② target_date 当天: 两种买入路径 ====================
                if today == target_date:
                    executed = False
                    
                    # 【路径 A】信号优先: 检查最新信号文件中的量比是否达标
                    try:
                        # 从 signals 目录读取该股票的最新信号，获取当前量比
                        current_volume_ratio = self._get_latest_volume_ratio(code)
                        
                        if current_volume_ratio is not None and current_volume_ratio > 0:
                            # 关键判断：量比是否达到触发阈值
                            trigger_vr = item.get('trigger_volume_ratio', 18.0)
                            
                            if current_volume_ratio >= trigger_vr:
                                if logger:
                                    logger.log(f"[延时策略-信号优先] {code} 量比 {current_volume_ratio:.2f} >= 阈值 {trigger_vr:.2f},立即买入")
                                self._execute_buy(code, item)
                                codes_to_remove.append(code)
                                executed = True
                            else:
                                if logger:
                                    logger.log(f"[延时策略-量比不足] {code} 当前量比 {current_volume_ratio:.2f} < 阈值 {trigger_vr:.2f},继续等待")
                        else:
                            if logger:
                                logger.log(f"[延时策略-无信号] {code} 未找到最新信号数据,继续等待")
                    except Exception as e:
                        if logger:
                            logger.log(f"[警告] {code} 检查量比失败: {e}")
                    
                    if executed:
                        continue

                    # 【路径 B】保底机制: 14:39 之后强制买入
                    if now_time >= "1439":
                        if logger:
                            logger.log(f"[延时策略-保底买入] {code} 到达执行时间(14:39),执行保底买入")
                        self._execute_buy(code, item)
                        codes_to_remove.append(code)
                        continue
                    
                    # 还没到14:39,继续等待
                    if logger:
                        logger.log(f"[延时策略-等待中] {code} 目标日但未触发(当前{now_time}),继续等待")
                    continue
                
                # ==================== ③ target_date 之后: 延时策略过期 ====================
                if today > target_date:
                    if logger:
                        logger.log(f"[延时策略-已过期] {code} 目标日={target_date}, 今天={today}, 自动删除(不再买入)")
                    codes_to_remove.append(code)
                    continue
                    
            except Exception as e:
                if logger:
                    logger.log(f"[错误] 处理股票异常: {e}")
                    
        # 清理名单(买入后或删除过期)
        for code in codes_to_remove:
            if code in self.delayed_watchlist['watchlist']:
                del self.delayed_watchlist['watchlist'][code]
        if codes_to_remove:
            self._save_watchlist()
            if logger:
                logger.log(f"[延时策略-清理] 已移除 {len(codes_to_remove)} 只股票")

    def _execute_buy(self, code, item):
        """执行延时策略的买入操作"""
        logger = get_logger()
        try:
            # 【修复】使用真正的实时行情API获取价格
            latest_prices = self.engine.get_latest_prices([code])
            current_price = latest_prices.get(code)
            limit_up = 0  # 延时策略暂不需要涨停价
            
            if current_price is None or current_price <= 0:
                current_price = item.get('trigger_price', 0)
                
            if current_price <= 0:
                if logger:
                    logger.log(f"[错误] {code} 价格无效，放弃买入")
                return False
            
            # 资产查询
            asset = self.engine.query_asset()
            if not asset:
                return False
            
            available_cash = asset.get('cash', 0) * 0.98
            
            SINGLE_ORDER_CASH_RATIO = 0.8
            FIXED_ORDER_AMOUNT = 50000.0
            MIN_ORDER_VALUE = 15000
            
            if available_cash < MIN_ORDER_VALUE:
                return False
                
            target_cash = min(available_cash * SINGLE_ORDER_CASH_RATIO, FIXED_ORDER_AMOUNT)
            if target_cash < MIN_ORDER_VALUE:
                target_cash = available_cash
                
            vol = int((target_cash / current_price) // 100) * 100
            if vol < 100:
                if available_cash >= current_price * 100:
                    vol = 100
                else:
                    return False
                    
            # 下单定价
            order_price = round(current_price * 1.01, 2)
            
            if limit_up > 0 and order_price > limit_up:
                order_price = limit_up
                
            # 执行下单
            success = self.engine.order_stock(code, "BUY", vol, order_price, "DELAYED_V9")
            
            if logger:
                logger.log(f"[下单] {code} 买入 {vol} 股 @ {order_price:.2f} 元")
                
            return success
            
        except Exception as e:
            if logger:
                logger.log(f"[异常] {code} 买入失败: {e}")
            return False

    def execute(self):
        """执行延时策略"""
        logger = get_logger()
        if logger:
            logger.log("---- 开始执行延时策略 ----")
        self.check_and_execute()
        if logger:
            logger.log("---- 执行结束 ----")

    def process_recent_signals(self):
        """处理最近收到的信号（简化版）"""
        pass
