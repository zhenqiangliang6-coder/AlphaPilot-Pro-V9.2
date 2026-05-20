# -*- coding: utf-8 -*-
import imaplib
import email
from bs4 import BeautifulSoup
import json
import os
import time
import re
from datetime import datetime
from html import unescape
import hashlib

# ================= 【多邮箱配置区域】 =================
EMAIL_ACCOUNTS = [
    {
        "label": "QQ-主",
        "type": "imap",
        "user": "497720537@qq.com",
        "password": "********khacach",  # ← 替换为16位授权码（去掉空格）
        "imap_server": "imap.qq.com"
    },
    {
        "label": "QQ-备用",
        "type": "imap",
        "user": "*****anbadavid@qq.com",
        "password": "*******eaha",  # ← 替换为16位授权码（去掉空格）
        "imap_server": "imap.qq.com"
    }
]

# ================= 【路径配置】 =================
# 【修复】使用项目根目录，与 main.py 保持一致
import os
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))  # d:\mpython
SIGNAL_DIR = os.path.join(PROJECT_ROOT, "signals")  # d:\mpython\signals
LOG_DIR = os.path.join(PROJECT_ROOT, "logs_receiver")  # d:\mpython\logs_receiver
PROCESSED_IDS_FILE = os.path.join(SIGNAL_DIR, ".processed_email_ids.json")
HASH_RECORD_FILE = os.path.join(SIGNAL_DIR, ".processed_signal_hashes.json")

# 策略配置
MIN_RATIO_THRESHOLD = None  # 接收端不过滤，完全信任发送端

# ================= 【工具函数】 =================
def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(SIGNAL_DIR, exist_ok=True)
    os.makedirs(os.path.join(SIGNAL_DIR, "processed"), exist_ok=True)
    log_file = os.path.join(LOG_DIR, f"receiver_{datetime.now().strftime('%Y%m%d')}.log")
    return log_file

def log_message(msg, log_file):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {msg}"
    print(log_line)
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    except Exception as e:
        print(f"Log write failed: {e}")

def load_json_set(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except Exception as e:
            log_message(f"读取记录文件失败 {file_path}: {e}", log_file)
            return set()
    return set()

def save_json_set(file_path, data_set, max_keep=None):
    data_list = list(data_set)
    if max_keep is not None and len(data_list) > max_keep:
        data_list = data_list[-max_keep:]
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, ensure_ascii=False)
    except Exception as e:
        log_message(f"保存记录文件失败 {file_path}: {e}", log_file)

def load_processed_ids(file_path):
    return load_json_set(file_path)

def save_processed_id(file_path, email_id):
    ids = load_processed_ids(file_path)
    ids.add(email_id)
    save_json_set(file_path, ids, max_keep=1000)

def load_processed_hashes(file_path):
    return load_json_set(file_path)

def save_processed_hash(file_path, hash_value):
    hashes = load_processed_hashes(file_path)
    hashes.add(hash_value)
    save_json_set(file_path, hashes, max_keep=2000)

def calc_signals_hash(signals):
    raw = json.dumps(signals, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(raw.encode('utf-8')).hexdigest()

def normalize_stock_code(code_str, log_file):
    """
    将股票代码转换为掘金标准格式
    
    支持格式：
    - "300444" -> "SZSE.300444"
    - "603353" -> "SHSE.603353"
    - "300444.SZ" -> "SZSE.300444" (自动转换)
    - "603353.SH" -> "SHSE.603353" (自动转换)
    """
    code_str = str(code_str).strip()
    
    # 如果包含 .SH/.SZ/.BJ，先提取纯数字部分
    if '.SH' in code_str or '.SZ' in code_str or '.BJ' in code_str:
        code_str = code_str.split('.')[0]
    
    # 如果不是纯数字，尝试提取数字
    if not code_str.isdigit():
        match = re.search(r'(\d+)', code_str)
        if match:
            code_str = match.group(1)
        else:
            return None
    
    # 根据代码前缀判断交易所并返回掘金标准格式
    if code_str.startswith(('60', '68', '51', '56')):
        return f"SHSE.{code_str}"
    elif code_str.startswith(('00', '30', '15')):
        return f"SZSE.{code_str}"
    elif code_str.startswith(('43', '83', '87')):
        return f"BJ.{code_str}"
    else:
        log_message(f" 未知代码前缀: {code_str}, 默认视为 SHSE", log_file)
        return f"SHSE.{code_str}"

# ================= 【核心解析逻辑】 =================
def parse_html_table(html_content, log_file):
    """解析神经元视图 HTML 表格（专家级动态列识别）"""
    soup = BeautifulSoup(html_content, 'lxml')
    tables = soup.find_all('table')
    if not tables:
        log_message(" 未在视图中找到任何表格", log_file)
        return []
    
    table = tables[0]
    rows = table.find_all('tr')
    if len(rows) <= 1:
        return []

    signals = []
    log_message(f" 发现表格，共 {len(rows)-1} 行数据", log_file)

    # --- 【核心改动】动态列索引映射 ---
    header_row = rows[0]
    header_cols = header_row.find_all(['td', 'th'])
    # 提取表头文本并清洗
    headers = [unescape(col.get_text(strip=True)).strip() for col in header_cols]
    
    # 定义我们需要匹配的列名（请确保这里的汉字和你发送端表头的汉字完全一致）
    COL_CODE = "股票代码"
    COL_NAME = "股票名称"
    COL_ACTION = "信号"
    COL_PRICE = "当前价格"
    COL_RATIO = "量比" # 关键：无论它在第几列，只要表头写着“量比”就能找到

    try:
        # 动态查找列索引
        idx_code = headers.index(COL_CODE)
        idx_name = headers.index(COL_NAME)
        idx_action = headers.index(COL_ACTION)
        idx_price = headers.index(COL_PRICE)
        idx_ratio = headers.index(COL_RATIO)
        
        log_message(f" 动态索引映射: {headers}", log_file)
        
    except ValueError as e:
        log_message(f" 表头映射失败，未找到指定列名。当前表头: {headers}", log_file)
        return []

    # --- 解析数据行 ---
    for i, row in enumerate(rows[1:], start=1):
        cols = row.find_all(['td', 'th'])
        # 检查列数是否足够
        if len(cols) <= max(idx_code, idx_name, idx_action, idx_price, idx_ratio):
            log_message(f" [行{i}] 列数不足，跳过", log_file)
            continue

        try:
            raw_code = unescape(cols[idx_code].get_text(strip=True))
            raw_name = unescape(cols[idx_name].get_text(strip=True))
            raw_action = unescape(cols[idx_action].get_text(strip=True))
            raw_price = unescape(cols[idx_price].get_text(strip=True)).replace(',', '')
            raw_ratio = unescape(cols[idx_ratio].get_text(strip=True)).replace(',', '')

            if not raw_code or not raw_price or not raw_ratio:
                raise ValueError("关键字段为空")

            price = float(raw_price)
            ratio = float(raw_ratio)

            # 接收端过滤逻辑 (如果配置了阈值)
            if MIN_RATIO_THRESHOLD is not None and ratio < MIN_RATIO_THRESHOLD:
                log_message(f" [行{i}] 过滤: {raw_code} (量比={ratio} < {MIN_RATIO_THRESHOLD})", log_file)
                continue

            full_code = normalize_stock_code(raw_code, log_file)
            if not full_code:
                log_message(f" [行{i}] 代码格式无效: {raw_code}", log_file)
                continue

            # 动作识别
            action = "HOLD"
            if "买入" in raw_action or "BUY" in raw_action.upper():
                action = "BUY"
            elif "卖出" in raw_action or "SELL" in raw_action.upper():
                action = "SELL"

            signal_obj = {
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "code": full_code,
                "name": raw_name,
                "action": action,
                "price": price,
                "volume_ratio": ratio,
                "source": "AlphaPilot_Email"
            }
            signals.append(signal_obj)
            log_message(f" [行{i}] 解析成功: {full_code} [{raw_name}] {action} @ {price} (VR:{ratio})", log_file)

        except Exception as e:
            log_message(f" [行{i}] 解析失败: {str(e)}", log_file)

    return signals

def save_signals_to_txt(signals, log_file):
    if not signals:
        log_message(" 本次没有有效因子被保存。", log_file)
        return False

    # --- 【核心改动】基于内容的去重 (防止双邮箱重复下单) ---
    hash_value = calc_signals_hash(signals)
    existing_hashes = load_processed_hashes(HASH_RECORD_FILE)
    
    if hash_value in existing_hashes:
        log_message("本批信号内容已存在（哈希重复），跳过保存（防双邮箱重复）", log_file)
        return False

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"signal_batch_{timestamp}.txt"
    filepath = os.path.join(SIGNAL_DIR, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            for sig in signals:
                line = json.dumps(sig, ensure_ascii=False)
                f.write(line + '\n')
        save_processed_hash(HASH_RECORD_FILE, hash_value)
        log_message(f"成功保存 {len(signals)} 条因子至: {filename}", log_file)
        return True
    except Exception as e:
        log_message(f" 保存文件失败: {e}", log_file)
        return False

# ================= 【主流程：单账号处理】 =================
def fetch_and_process_emails_for_account(log_file, account):
    processed_ids = load_processed_ids(PROCESSED_IDS_FILE)
    mail = None
    try:
        log_message(f" 正在连接 {account['label']} 邮箱服务器 ({account['user']}) ...", log_file)
        mail = imaplib.IMAP4_SSL(account["imap_server"], timeout=20)
        mail.login(account["user"], account["password"])

        # 选择收件箱 (兼容性处理)
        status, data = mail.select('"INBOX"')
        if status != "OK":
            log_message(f" {account['label']} 使用 '\"INBOX\"' 失败，尝试 'INBOX'...", log_file)
            status, data = mail.select("INBOX")
        if status != "OK":
            log_message(f" {account['label']} 无法选择文件夹: {data}", log_file)
            return

        mail.noop()
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            log_message(f" {account['label']} 搜索因子失败", log_file)
            return
            
        email_ids = messages[0].split()
        if not email_ids:
            # log_message(f" {account['label']} 当前没有未读邮件", log_file) # 频繁轮询时不打印此日志，减少干扰
            return

        new_count = 0
        for e_id in email_ids:
            eid_str = e_id.decode('utf-8')
            if eid_str in processed_ids:
                mail.store(e_id, '+FLAGS', '\\Seen')
                continue

            try:
                res, msg_data = mail.fetch(e_id, "(RFC822)")
                if res != "OK":
                    continue
                    
                raw_email = msg_data[0][1]
                email_msg = email.message_from_bytes(raw_email)
                subject = email_msg.get('subject', 'No Subject')
                log_message(f" {account['label']} 正在解析因子: {subject}", log_file)

                html_content = ""
                if email_msg.is_multipart():
                    for part in email_msg.walk():
                        ctype = part.get_content_type()
                        cdispo = str(part.get("Content-Disposition"))
                        if ctype == "text/html" and "attachment" not in cdispo:
                            try:
                                charset = part.get_content_charset() or 'utf-8'
                                payload = part.get_payload(decode=True)
                                if payload:
                                    html_content = payload.decode(charset, errors='ignore')
                                break
                            except Exception as e:
                                log_message(f" 解码 HTML 失败: {e}", log_file)
                else:
                    if email_msg.get_content_type() == "text/html":
                        try:
                            charset = email_msg.get_content_charset() or 'utf-8'
                            payload = email_msg.get_payload(decode=True)
                            if payload:
                                html_content = payload.decode(charset, errors='ignore')
                        except:
                            pass

                if html_content and "<table" in html_content:
                    signals = parse_html_table(html_content, log_file)
                    if signals:
                        if save_signals_to_txt(signals, log_file):
                            mail.store(e_id, '+FLAGS', '\\Seen')
                            save_processed_id(PROCESSED_IDS_FILE, eid_str)
                            new_count += 1
                            log_message(f" {account['label']} 邮件 {eid_str} 处理完成", log_file)
                        else:
                            log_message(f" {account['label']} 邮件 {eid_str} 保存因子失败", log_file)
                    else:
                        log_message(f"{account['label']} 邮件 {eid_str} 无有效信号", log_file)
                        mail.store(e_id, '+FLAGS', '\\Seen')
                        save_processed_id(PROCESSED_IDS_FILE, eid_str)
                else:
                    log_message(f" {account['label']} 邮件 {eid_str} 无 HTML 表格", log_file)
                    mail.store(e_id, '+FLAGS', '\\Seen')
                    save_processed_id(PROCESSED_IDS_FILE, eid_str)

            except Exception as e_inner:
                log_message(f" {account['label']} 处理单封邮件出错: {e_inner}", log_file)
                # 即使单封邮件出错，也标记为已读，防止死循环
                try:
                    mail.store(e_id, '+FLAGS', '\\Seen')
                    save_processed_id(PROCESSED_IDS_FILE, eid_str)
                except:
                    pass

        if new_count > 0:
            log_message(f" {account['label']} 本轮共成功处理 {new_count} 封有效信号邮件", log_file)

    except Exception as e:
        log_message(f" {account['label']} 因子处理主循环异常: {e}", log_file)
        time.sleep(10)
    finally:
        if mail:
            try:
                mail.close()
                mail.logout()
            except:
                pass

# ================= 【总入口：轮询所有邮箱】 =================
if __name__ == "__main__":
    LOG_FILE = setup_logging()
    log_message(" AlphaPilot 监听服务 (Pro 多邮箱版) 启动...", LOG_FILE)
    log_message(f" 信号保存目录: {SIGNAL_DIR}", LOG_FILE)
    log_message(f" 日志文件: {LOG_FILE}", LOG_FILE)
    
    while True:
        for acc in EMAIL_ACCOUNTS:
            fetch_and_process_emails_for_account(LOG_FILE, acc)
        time.sleep(35)
