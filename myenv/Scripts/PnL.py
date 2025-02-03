import re
import csv
from datetime import datetime

# Files
TRADE_LOG_FILE = "flight_risk_trade_log.txt"
SUMMARY_LOG_FILE = "flight_risk_trade_summary.txt"
REPORT_FILE = "flight_risk_trade_report.txt"
BALANCE_CSV_FILE = "flight_risk_balance_over_time.csv"

# Initial Cash Balance
starting_balance = 53100  # Adjust as needed
balance = starting_balance

# Data Structures for tracking positions and trade history
positions = {}
trade_history = []
realized_pnl = 0

# Performance Metrics
win_count = 0
loss_count = 0
total_trades = 0
total_contracts = 0
holding_times = []
best_trade = None
worst_trade = None

# Write initial balance to CSV
with open(BALANCE_CSV_FILE, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["timestamp", "balance", "realized_pnl", "total_trades"])
    writer.writerow([datetime.now().isoformat(), balance, realized_pnl, total_trades])

# Regex Patterns
open_pattern = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - Opening (\d+) (Yes|No): Market (\S+), My Odds ([\d.]+), Market (Ask|Bid) (\d+), Time (\S+)"
)
close_pattern = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - Closing all (Yes|No): Market (\S+), My Odds ([\d.]+), Market (Bid|Ask) (\d+), Time (\S+)"
)

# Process trade log
with open(TRADE_LOG_FILE, "r") as file:
    for line in file:
        line = line.strip()
        open_match = open_pattern.search(line)
        close_match = close_pattern.search(line)
        
        if open_match:
            log_time, size_str, side, market, my_odds, price_label, price_str, entry_time_str = open_match.groups()
            size = int(size_str)
            price = int(price_str)
            cost = size * price
            
            if balance >= cost:
                balance -= cost
                total_contracts += size
                for _ in range(size):
                    positions.setdefault(market, []).append({"side": side, "entry_price": price, "timestamp": entry_time_str})
            
        elif close_match:
            log_time, side, market, my_odds, price_label, price_str, exit_time_str = close_match.groups()
            exit_price = int(price_str)
            
            if market in positions:
                open_positions = positions[market]
                matching_positions = [p for p in open_positions if p["side"] == side]
                
                for pos in matching_positions:
                    entry_price = pos["entry_price"]
                    entry_time = datetime.fromisoformat(pos["timestamp"])
                    exit_dt = datetime.fromisoformat(exit_time_str)
                    holding_time = (exit_dt - entry_time).total_seconds()
                    holding_times.append(holding_time)
                    
                    pnl = (exit_price - entry_price)
                    realized_pnl += pnl
                    balance += exit_price
                    trade_history.append((market, side, entry_price, exit_price, pnl, holding_time))
                    
                    if best_trade is None or pnl > best_trade[4]:
                        best_trade = (market, side, entry_price, exit_price, pnl, holding_time)
                    if worst_trade is None or pnl < worst_trade[4]:
                        worst_trade = (market, side, entry_price, exit_price, pnl, holding_time)
                    
                    win_count += 1 if pnl > 0 else 0
                    loss_count += 1 if pnl <= 0 else 0
                    total_trades += 1
                
                positions[market] = [p for p in open_positions if p["side"] != side]
            
        # Log balance after each trade
        with open(BALANCE_CSV_FILE, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([datetime.now().isoformat(), balance, realized_pnl, total_trades])

# Compute Summary Metrics
average_holding_time = sum(holding_times) / len(holding_times) if holding_times else 0

# Write Trade Summary to File
with open(SUMMARY_LOG_FILE, "w") as f:
    f.write(f"Total Realized PnL: {realized_pnl}\n")
    f.write(f"Total Trades: {total_trades}\n")
    f.write(f"Total Contracts Traded: {total_contracts}\n")
    f.write(f"Average Holding Time: {average_holding_time:.2f} seconds\n")
    
    if best_trade:
        f.write(f"Best Trade: {best_trade}\n")
    if worst_trade:
        f.write(f"Worst Trade: {worst_trade}\n")
    
    f.write("\nTrade History:\n")
    for trade in trade_history:
        f.write(f"{trade}\n")

# Write Abbreviated Trade Report
with open(REPORT_FILE, "w") as f:
    f.write("Market                       | Side | Entry | Exit | PnL   | Holding Time (s)\n")
    f.write("--------------------------------------------------------------------------\n")
    for trade in trade_history:
        market, side, entry_price, exit_price, pnl, hold_time = trade
        f.write(f"{market:<25} | {side:<3} | {entry_price:<5} | {exit_price:<4} | {pnl:<5} | {hold_time:.2f}\n")

print(f"Trade summary saved to {SUMMARY_LOG_FILE}")
print(f"Abbreviated report saved to {REPORT_FILE}")
print(f"Balance over time saved to {BALANCE_CSV_FILE}")
