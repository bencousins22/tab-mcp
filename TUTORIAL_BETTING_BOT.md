# Tutorial: Building an Intelligent Betting Bot

## Overview

In this comprehensive tutorial, you'll build a fully functional betting analysis bot that:

- 🔍 Analyzes racing form data automatically
- 📊 Calculates value bets using statistical models
- 🎯 Identifies high-probability opportunities
- 💰 Tracks bankroll and bet history
- 📈 Provides performance analytics
- ⚠️ Implements risk management rules

**Difficulty**: Intermediate  
**Time**: 2-3 hours  
**Prerequisites**: Python basics, API understanding

---

## What You'll Build

A command-line betting bot with these features:

1. **Form Analysis Engine**: Evaluates horse/runner performance
2. **Value Calculator**: Identifies overlay bets (odds > probability)
3. **Risk Manager**: Kelly Criterion for bet sizing
4. **Data Tracker**: SQLite database for bet history
5. **Performance Reporter**: Win rate, ROI, profit/loss tracking

---

## Project Structure

```
betting-bot/
├── bot.py                 # Main bot logic
├── form_analyzer.py       # Form analysis engine
├── value_calculator.py    # Value betting logic
├── risk_manager.py        # Bankroll and risk management
├── database.py            # Data persistence
├── config.py              # Configuration
├── requirements.txt       # Dependencies
├── .env                   # Credentials (gitignored)
└── README.md              # Bot documentation
```

---

## Step 1: Setup

### Install Dependencies

Create `requirements.txt`:

```txt
tab-mcp>=1.0.0
python-dotenv>=1.0.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
sqlalchemy>=2.0.0
tabulate>=0.9.0
```

Install:
```bash
pip install -r requirements.txt
```

### Configure Environment

Create `.env`:

```bash
TAB_CLIENT_ID=your_client_id
TAB_CLIENT_SECRET=your_client_secret
TAB_USERNAME=your_account  # For betting (optional)
TAB_PASSWORD=your_password  # For betting (optional)
DEFAULT_JURISDICTION=NSW
INITIAL_BANKROLL=1000.00
MAX_BET_PERCENTAGE=0.02  # 2% max per bet
```

---

## Step 2: Configuration Module

Create `config.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Bot configuration settings"""

    # API Credentials
    CLIENT_ID = os.getenv("TAB_CLIENT_ID")
    CLIENT_SECRET = os.getenv("TAB_CLIENT_SECRET")
    USERNAME = os.getenv("TAB_USERNAME")
    PASSWORD = os.getenv("TAB_PASSWORD")

    # Betting Parameters
    INITIAL_BANKROLL = float(os.getenv("INITIAL_BANKROLL", "1000"))
    MAX_BET_PERCENTAGE = float(os.getenv("MAX_BET_PERCENTAGE", "0.02"))
    MIN_VALUE_THRESHOLD = 0.1  # 10% overlay minimum
    MIN_CONFIDENCE = 0.6  # 60% win probability minimum

    # Racing Filters
    DEFAULT_JURISDICTION = os.getenv("DEFAULT_JURISDICTION", "NSW")
    RACE_TYPES = ["R"]  # Thoroughbred only
    MIN_FIELD_SIZE = 6
    MAX_FIELD_SIZE = 18

    # Database
    DB_PATH = "betting_bot.db"

    # MCP Server
    MCP_SERVER_URL = os.getenv(
        "MCP_SERVER_URL",
        "https://server.smithery.ai/@bencousins22/tab-mcp/mcp"
    )
```

---

## Step 3: Database Module

Create `database.py`:

```python
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd

class BettingDatabase:
    """Manages bet history and analytics"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Bets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                meeting_name TEXT NOT NULL,
                race_number INTEGER NOT NULL,
                runner_number INTEGER NOT NULL,
                runner_name TEXT NOT NULL,
                odds REAL NOT NULL,
                stake REAL NOT NULL,
                win_probability REAL NOT NULL,
                expected_value REAL NOT NULL,
                result TEXT,  -- 'win', 'loss', 'pending'
                profit_loss REAL,
                notes TEXT
            )
        """)

        # Bankroll history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bankroll (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                balance REAL NOT NULL,
                change REAL NOT NULL,
                reason TEXT
            )
        """)

        conn.commit()
        conn.close()

    def add_bet(self, bet_data: Dict) -> int:
        """Record a new bet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO bets (
                timestamp, meeting_name, race_number, runner_number,
                runner_name, odds, stake, win_probability,
                expected_value, result
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            bet_data["meeting_name"],
            bet_data["race_number"],
            bet_data["runner_number"],
            bet_data["runner_name"],
            bet_data["odds"],
            bet_data["stake"],
            bet_data["win_probability"],
            bet_data["expected_value"],
            "pending"
        ))

        bet_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return bet_id

    def update_bet_result(self, bet_id: int, won: bool, dividend: float = None):
        """Update bet result after race"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get bet details
        cursor.execute("SELECT stake, odds FROM bets WHERE id = ?", (bet_id,))
        stake, odds = cursor.fetchone()

        if won:
            profit_loss = (dividend or odds) * stake - stake
            result = "win"
        else:
            profit_loss = -stake
            result = "loss"

        cursor.execute("""
            UPDATE bets
            SET result = ?, profit_loss = ?
            WHERE id = ?
        """, (result, profit_loss, bet_id))

        conn.commit()
        conn.close()

    def get_statistics(self) -> Dict:
        """Calculate betting statistics"""
        conn = sqlite3.connect(self.db_path)

        # Get all completed bets
        df = pd.read_sql_query(
            "SELECT * FROM bets WHERE result IN ('win', 'loss')",
            conn
        )

        if len(df) == 0:
            return {
                "total_bets": 0,
                "win_rate": 0,
                "roi": 0,
                "total_profit": 0
            }

        stats = {
            "total_bets": len(df),
            "wins": len(df[df["result"] == "win"]),
            "losses": len(df[df["result"] == "loss"]),
            "win_rate": len(df[df["result"] == "win"]) / len(df),
            "total_staked": df["stake"].sum(),
            "total_profit": df["profit_loss"].sum(),
            "average_odds": df["odds"].mean(),
            "average_stake": df["stake"].mean(),
        }

        stats["roi"] = (stats["total_profit"] / stats["total_staked"]) * 100

        conn.close()
        return stats

    def get_recent_bets(self, limit: int = 10) -> pd.DataFrame:
        """Get recent bets"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(
            f"SELECT * FROM bets ORDER BY timestamp DESC LIMIT {limit}",
            conn
        )
        conn.close()
        return df
```

---

## Step 4: Form Analyzer

Create `form_analyzer.py`:

```python
import numpy as np
from typing import Dict, List
import asyncio
from mcp.client import Client

class FormAnalyzer:
    """Analyzes racing form to predict win probabilities"""

    def __init__(self, client: Client, access_token: str):
        self.client = client
        self.token = access_token

    async def analyze_race(self, meeting_id: str, race_number: int) -> Dict:
        """Analyze all runners in a race"""

        # Get race details
        race = await self.client.call_tool(
            "racing_get_race",
            {
                "access_token": self.token,
                "meeting_id": meeting_id,
                "race_number": race_number,
                "fixed_odds": True
            }
        )

        # Get form guide
        form = await self.client.call_tool(
            "racing_get_race_form",
            {
                "access_token": self.token,
                "meeting_id": meeting_id,
                "race_number": race_number
            }
        )

        # Analyze each runner
        runner_predictions = []
        for runner in race.get("runners", []):
            prediction = await self._analyze_runner(
                meeting_id,
                race_number,
                runner["runner_number"],
                runner,
                form
            )
            runner_predictions.append(prediction)

        return {
            "race": race,
            "predictions": runner_predictions
        }

    async def _analyze_runner(
        self,
        meeting_id: str,
        race_number: int,
        runner_number: int,
        runner_data: Dict,
        form_data: Dict
    ) -> Dict:
        """Analyze individual runner"""

        # Get detailed runner form
        try:
            runner_form = await self.client.call_tool(
                "racing_get_runner_form",
                {
                    "access_token": self.token,
                    "meeting_id": meeting_id,
                    "race_number": race_number,
                    "runner_number": runner_number
                }
            )
        except:
            runner_form = {}

        # Calculate form score (0-1)
        form_score = self._calculate_form_score(runner_data, runner_form)

        # Calculate class score
        class_score = self._calculate_class_score(runner_data)

        # Calculate jockey/trainer score  
        connections_score = self._calculate_connections_score(runner_data)

        # Calculate barrier score
        barrier_score = self._calculate_barrier_score(
            runner_data.get("barrier"),
            len(form_data.get("runners", []))
        )

        # Weighted combination
        win_probability = (
            form_score * 0.40 +
            class_score * 0.25 +
            connections_score * 0.20 +
            barrier_score * 0.15
        )

        return {
            "runner_number": runner_number,
            "runner_name": runner_data.get("runner_name", "Unknown"),
            "odds": runner_data.get("odds", 0),
            "win_probability": win_probability,
            "form_score": form_score,
            "class_score": class_score,
            "connections_score": connections_score,
            "barrier_score": barrier_score
        }

    def _calculate_form_score(self, runner: Dict, form: Dict) -> float:
        """Calculate recent form score"""
        # Parse last 5 starts (e.g., "1-2-1-3-1")
        last_starts = runner.get("last_5_starts", "")
        if not last_starts:
            return 0.5  # Neutral if no form

        positions = []
        for char in last_starts.replace("-", ""):
            if char.isdigit():
                positions.append(int(char))

        if not positions:
            return 0.5

        # Score based on average position (1st=1.0, 10th+=0.0)
        avg_position = np.mean(positions)
        score = max(0, 1 - (avg_position - 1) / 9)

        return score

    def _calculate_class_score(self, runner: Dict) -> float:
        """Calculate class/prize money score"""
        career_stats = runner.get("career_stats", {})
        prize_money = career_stats.get("prize_money", 0)

        # Normalize prize money to 0-1 scale
        # $0 = 0.3, $1M+ = 1.0
        if prize_money == 0:
            return 0.3

        score = min(1.0, 0.3 + (prize_money / 1000000) * 0.7)
        return score

    def _calculate_connections_score(self, runner: Dict) -> float:
        """Calculate jockey/trainer score"""
        # In real implementation, would track jockey/trainer stats
        # For now, use simple heuristic
        return 0.6  # Neutral

    def _calculate_barrier_score(self, barrier: int, field_size: int) -> float:
        """Calculate barrier advantage"""
        if not barrier or not field_size:
            return 0.5

        # Middle barriers slightly better
        ideal_barrier = field_size / 2
        distance = abs(barrier - ideal_barrier)
        score = max(0.3, 1 - (distance / field_size))

        return score
```

---

## Step 5: Value Calculator

Create `value_calculator.py`:

```python
from typing import Dict, List, Optional
import numpy as np

class ValueCalculator:
    """Identifies value betting opportunities"""

    def __init__(self, min_value_threshold: float = 0.1):
        self.min_value_threshold = min_value_threshold

    def find_value_bets(self, predictions: List[Dict]) -> List[Dict]:
        """Identify runners with positive expected value"""
        value_bets = []

        for prediction in predictions:
            value_analysis = self.analyze_value(prediction)

            if value_analysis["has_value"]:
                value_bets.append({
                    **prediction,
                    **value_analysis
                })

        # Sort by expected value
        value_bets.sort(key=lambda x: x["expected_value"], reverse=True)

        return value_bets

    def analyze_value(self, prediction: Dict) -> Dict:
        """Analyze single runner for value"""
        odds = prediction["odds"]
        win_prob = prediction["win_probability"]

        # Implied probability from odds
        implied_prob = 1 / odds if odds > 0 else 0

        # Expected value = (probability × (odds - 1)) - (1 - probability)
        expected_value = (win_prob * (odds - 1)) - (1 - win_prob)

        # Value percentage
        value_percentage = (win_prob - implied_prob) / implied_prob if implied_prob > 0 else 0

        has_value = (
            expected_value > 0 and
            value_percentage >= self.min_value_threshold
        )

        return {
            "has_value": has_value,
            "expected_value": expected_value,
            "value_percentage": value_percentage,
            "implied_probability": implied_prob,
            "overlay": win_prob - implied_prob
        }

    def calculate_optimal_stake(
        self,
        bankroll: float,
        odds: float,
        win_probability: float,
        max_bet_pct: float = 0.02
    ) -> float:
        """Calculate optimal bet size using Kelly Criterion"""

        # Kelly Criterion: f = (bp - q) / b
        # where f = fraction of bankroll
        #       b = odds - 1 (profit on $1 bet)
        #       p = win probability
        #       q = 1 - p (loss probability)

        b = odds - 1
        p = win_probability
        q = 1 - p

        kelly_fraction = (b * p - q) / b

        # Fractional Kelly (use 25% of full Kelly for safety)
        safe_kelly = kelly_fraction * 0.25

        # Apply max bet limit
        final_fraction = min(safe_kelly, max_bet_pct)

        # Ensure positive and reasonable
        final_fraction = max(0, min(final_fraction, max_bet_pct))

        stake = bankroll * final_fraction

        # Round to 2 decimal places
        return round(stake, 2)
```

Continuing in next response...


---

## Step 6: Risk Manager

Create `risk_manager.py`:

```python
from typing import Dict, Optional
import json
from datetime import datetime

class RiskManager:
    """Manages bankroll and betting risk"""

    def __init__(self, initial_bankroll: float, max_bet_pct: float = 0.02):
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.max_bet_pct = max_bet_pct
        self.active_bets = []

    def can_place_bet(self, stake: float) -> tuple[bool, str]:
        """Check if bet can be placed"""

        # Check bankroll sufficient
        if stake > self.current_bankroll:
            return False, f"Insufficient bankroll: ${self.current_bankroll:.2f} < ${stake:.2f}"

        # Check max bet limit
        max_stake = self.current_bankroll * self.max_bet_pct
        if stake > max_stake:
            return False, f"Exceeds max bet: ${stake:.2f} > ${max_stake:.2f} (2% rule)"

        # Check exposure (total active bets)
        total_exposure = sum(bet["stake"] for bet in self.active_bets)
        if total_exposure + stake > self.current_bankroll * 0.1:  # Max 10% exposure
            return False, f"Exceeds exposure limit: total would be ${total_exposure + stake:.2f}"

        return True, "OK"

    def place_bet(self, bet_data: Dict) -> bool:
        """Record bet placement"""
        stake = bet_data["stake"]

        can_bet, reason = self.can_place_bet(stake)
        if not can_bet:
            print(f"❌ Cannot place bet: {reason}")
            return False

        # Deduct from bankroll
        self.current_bankroll -= stake

        # Add to active bets
        self.active_bets.append({
            "bet_id": bet_data.get("bet_id"),
            "stake": stake,
            "timestamp": datetime.now().isoformat()
        })

        return True

    def settle_bet(self, bet_id: int, profit_loss: float):
        """Settle completed bet"""
        # Remove from active bets
        self.active_bets = [b for b in self.active_bets if b.get("bet_id") != bet_id]

        # Update bankroll
        self.current_bankroll += profit_loss

    def get_status(self) -> Dict:
        """Get current risk status"""
        total_exposure = sum(bet["stake"] for bet in self.active_bets)

        return {
            "current_bankroll": self.current_bankroll,
            "initial_bankroll": self.initial_bankroll,
            "profit_loss": self.current_bankroll - self.initial_bankroll,
            "roi_pct": ((self.current_bankroll / self.initial_bankroll) - 1) * 100,
            "active_bets": len(self.active_bets),
            "total_exposure": total_exposure,
            "exposure_pct": (total_exposure / self.current_bankroll) * 100 if self.current_bankroll > 0 else 0,
            "available": self.current_bankroll - total_exposure
        }
```

---

## Step 7: Main Bot Logic

Create `bot.py`:

```python
import asyncio
from datetime import datetime
from typing import List, Dict
from mcp.client import Client
from tabulate import tabulate

from config import Config
from database import BettingDatabase
from form_analyzer import FormAnalyzer
from value_calculator import ValueCalculator
from risk_manager import RiskManager

class BettingBot:
    """Main betting bot orchestrator"""

    def __init__(self):
        self.config = Config()
        self.db = BettingDatabase(Config.DB_PATH)
        self.risk_manager = RiskManager(
            Config.INITIAL_BANKROLL,
            Config.MAX_BET_PERCENTAGE
        )
        self.value_calc = ValueCalculator(Config.MIN_VALUE_THRESHOLD)
        self.access_token = None
        self.client = None

    async def start(self):
        """Start the betting bot"""
        print("🤖 Betting Bot Starting...")
        print("="*60)

        async with Client(Config.MCP_SERVER_URL) as client:
            self.client = client

            # Authenticate
            await self._authenticate()

            # Main loop
            while True:
                try:
                    await self._run_analysis_cycle()

                    # Wait before next cycle
                    print("
⏳ Waiting 5 minutes before next scan...")
                    await asyncio.sleep(300)  # 5 minutes

                except KeyboardInterrupt:
                    print("

🛑 Bot stopped by user")
                    break
                except Exception as e:
                    print(f"
❌ Error in cycle: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute on error

    async def _authenticate(self):
        """Authenticate with Tabcorp API"""
        print("🔐 Authenticating...")

        auth_result = await self.client.call_tool(
            "tab_oauth_client_credentials",
            {
                "client_id": Config.CLIENT_ID,
                "client_secret": Config.CLIENT_SECRET
            }
        )

        self.access_token = auth_result["access_token"]
        print("✅ Authentication successful")

    async def _run_analysis_cycle(self):
        """Run one analysis cycle"""
        print(f"
{'='*60}")
        print(f"📊 Analysis Cycle: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        # Get next-to-go races
        races = await self._get_upcoming_races()

        if not races:
            print("⚠️  No upcoming races found")
            return

        print(f"
🏇 Found {len(races)} upcoming races")

        # Analyze each race
        all_opportunities = []
        for race in races[:3]:  # Analyze top 3 races
            opportunities = await self._analyze_race(
                race["meeting_id"],
                race["race_number"],
                race["meeting_name"]
            )
            all_opportunities.extend(opportunities)

        # Sort by value and display
        all_opportunities.sort(key=lambda x: x["expected_value"], reverse=True)

        if all_opportunities:
            self._display_opportunities(all_opportunities)

            # Auto-bet on top opportunity if configured
            if Config.AUTO_BET and all_opportunities:
                await self._place_bet(all_opportunities[0])
        else:
            print("
⚠️  No value opportunities found this cycle")

        # Display stats
        self._display_stats()

    async def _get_upcoming_races(self) -> List[Dict]:
        """Get next-to-go races"""
        result = await self.client.call_tool(
            "racing_get_next_to_go",
            {
                "access_token": self.access_token,
                "jurisdiction": Config.DEFAULT_JURISDICTION,
                "race_type": "R",
                "count": 5
            }
        )

        return result.get("races", [])

    async def _analyze_race(
        self,
        meeting_id: str,
        race_number: int,
        meeting_name: str
    ) -> List[Dict]:
        """Analyze a single race for value bets"""
        print(f"
📋 Analyzing: {meeting_name} Race {race_number}")

        # Create form analyzer
        analyzer = FormAnalyzer(self.client, self.access_token)

        # Get predictions
        analysis = await analyzer.analyze_race(meeting_id, race_number)

        # Find value bets
        value_bets = self.value_calc.find_value_bets(analysis["predictions"])

        # Add meeting context
        for bet in value_bets:
            bet["meeting_id"] = meeting_id
            bet["meeting_name"] = meeting_name
            bet["race_number"] = race_number

        if value_bets:
            print(f"  ✅ Found {len(value_bets)} value opportunities")
        else:
            print(f"  ❌ No value found")

        return value_bets

    def _display_opportunities(self, opportunities: List[Dict]):
        """Display betting opportunities in table format"""
        print("
" + "="*60)
        print("💎 VALUE BETTING OPPORTUNITIES")
        print("="*60)

        table_data = []
        for opp in opportunities[:5]:  # Top 5
            stake = self.value_calc.calculate_optimal_stake(
                self.risk_manager.current_bankroll,
                opp["odds"],
                opp["win_probability"],
                Config.MAX_BET_PERCENTAGE
            )

            table_data.append([
                f"{opp['meeting_name']} R{opp['race_number']}",
                f"#{opp['runner_number']} {opp['runner_name']}",
                f"{opp['odds']:.2f}",
                f"{opp['win_probability']*100:.1f}%",
                f"{opp['value_percentage']*100:.1f}%",
                f"${opp['expected_value']:.2f}",
                f"${stake:.2f}"
            ])

        headers = ["Race", "Runner", "Odds", "Win%", "Value%", "EV", "Stake"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

    async def _place_bet(self, opportunity: Dict):
        """Place a bet on an opportunity"""
        stake = self.value_calc.calculate_optimal_stake(
            self.risk_manager.current_bankroll,
            opportunity["odds"],
            opportunity["win_probability"],
            Config.MAX_BET_PERCENTAGE
        )

        print(f"
💰 Attempting to place bet:")
        print(f"   Runner: #{opportunity['runner_number']} {opportunity['runner_name']}")
        print(f"   Stake: ${stake:.2f}")
        print(f"   Expected Value: ${opportunity['expected_value']:.2f}")

        # Check with risk manager
        can_bet = self.risk_manager.place_bet({
            "stake": stake,
            "odds": opportunity["odds"]
        })

        if not can_bet:
            print("   ❌ Bet rejected by risk manager")
            return

        # Record in database
        bet_id = self.db.add_bet({
            "meeting_name": opportunity["meeting_name"],
            "race_number": opportunity["race_number"],
            "runner_number": opportunity["runner_number"],
            "runner_name": opportunity["runner_name"],
            "odds": opportunity["odds"],
            "stake": stake,
            "win_probability": opportunity["win_probability"],
            "expected_value": opportunity["expected_value"]
        })

        print(f"   ✅ Bet recorded (ID: {bet_id})")
        print(f"   📊 New bankroll: ${self.risk_manager.current_bankroll:.2f}")

    def _display_stats(self):
        """Display bot performance statistics"""
        risk_status = self.risk_manager.get_status()
        bet_stats = self.db.get_statistics()

        print("
" + "="*60)
        print("📈 PERFORMANCE STATISTICS")
        print("="*60)

        print("
💰 Bankroll:")
        print(f"   Current: ${risk_status['current_bankroll']:.2f}")
        print(f"   Initial: ${risk_status['initial_bankroll']:.2f}")
        print(f"   P/L: ${risk_status['profit_loss']:.2f} ({risk_status['roi_pct']:.2f}%)")
        print(f"   Active Bets: {risk_status['active_bets']}")
        print(f"   Exposure: ${risk_status['total_exposure']:.2f} ({risk_status['exposure_pct']:.1f}%)")

        if bet_stats["total_bets"] > 0:
            print("
📊 Betting Stats:")
            print(f"   Total Bets: {bet_stats['total_bets']}")
            print(f"   Wins: {bet_stats['wins']} ({bet_stats['win_rate']*100:.1f}%)")
            print(f"   Losses: {bet_stats['losses']}")
            print(f"   Total Staked: ${bet_stats['total_staked']:.2f}")
            print(f"   Total Profit: ${bet_stats['total_profit']:.2f}")
            print(f"   ROI: {bet_stats['roi']:.2f}%")
            print(f"   Avg Odds: {bet_stats['average_odds']:.2f}")
            print(f"   Avg Stake: ${bet_stats['average_stake']:.2f}")

if __name__ == "__main__":
    bot = BettingBot()
    asyncio.run(bot.start())
```

---

## Step 8: Running the Bot

### Start the Bot

```bash
python bot.py
```

### Expected Output

```
🤖 Betting Bot Starting...
============================================================
🔐 Authenticating...
✅ Authentication successful

============================================================
📊 Analysis Cycle: 2024-10-29 14:30:15
============================================================

🏇 Found 5 upcoming races

📋 Analyzing: Randwick Race 3
  ✅ Found 2 value opportunities

📋 Analyzing: Flemington Race 4
  ❌ No value found

📋 Analyzing: Eagle Farm Race 2
  ✅ Found 1 value opportunities

============================================================
💎 VALUE BETTING OPPORTUNITIES
============================================================
+------------------+--------------------+------+-------+--------+--------+--------+
| Race             | Runner             | Odds | Win%  | Value% | EV     | Stake  |
+==================+====================+======+=======+========+========+========+
| Randwick R3      | #5 Star Performer  | 4.50 | 28.5% | 22.3%  | $0.35  | $18.50 |
| Eagle Farm R2    | #2 Lightning Bolt  | 3.20 | 35.2% | 12.6%  | $0.28  | $22.00 |
| Randwick R3      | #1 Quick Silver    | 5.00 | 25.0% | 15.0%  | $0.25  | $15.00 |
+------------------+--------------------+------+-------+--------+--------+--------+

============================================================
📈 PERFORMANCE STATISTICS
============================================================

💰 Bankroll:
   Current: $982.50
   Initial: $1000.00
   P/L: $-17.50 (-1.75%)
   Active Bets: 3
   Exposure: $55.50 (5.7%)

📊 Betting Stats:
   Total Bets: 12
   Wins: 5 (41.7%)
   Losses: 7
   Total Staked: $215.00
   Total Profit: $-17.50
   ROI: -8.14%
   Avg Odds: 4.25
   Avg Stake: $17.92

⏳ Waiting 5 minutes before next scan...
```

---

## Step 9: Advanced Features

### Add Auto-Betting

Update `config.py`:

```python
class Config:
    # ... existing config ...

    # Auto-betting
    AUTO_BET = False  # Set True to enable automatic betting
    MIN_VALUE_FOR_AUTO_BET = 0.15  # 15% minimum value
    MAX_AUTO_BETS_PER_CYCLE = 2
```

### Add Bet Result Tracking

Create `result_tracker.py`:

```python
import asyncio
from typing import List
from datetime import datetime, timedelta

class ResultTracker:
    """Track and settle bet results"""

    def __init__(self, client, access_token, db, risk_manager):
        self.client = client
        self.token = access_token
        self.db = db
        self.risk_manager = risk_manager

    async def check_results(self):
        """Check results for pending bets"""
        pending = self.db.get_recent_bets(limit=50)
        pending = pending[pending["result"] == "pending"]

        for _, bet in pending.iterrows():
            # Check if race has resulted
            try:
                results = await self.client.call_tool(
                    "sports_get_resulted_match_in_competition",
                    {
                        "access_token": self.token,
                        "sport_id": "RACE",
                        "competition_id": bet["meeting_name"],
                        "match_id": f"{bet['race_number']}"
                    }
                )

                # Check if our runner won
                won = self._check_if_won(results, bet["runner_number"])

                # Update bet
                self.db.update_bet_result(bet["id"], won)

                # Update risk manager
                if won:
                    profit = bet["stake"] * (bet["odds"] - 1)
                else:
                    profit = -bet["stake"]

                self.risk_manager.settle_bet(bet["id"], profit)

                print(f"{'✅ WIN' if won else '❌ LOSS'}: {bet['runner_name']} - ${profit:.2f}")

            except Exception as e:
                # Race hasn't resulted yet
                continue

    def _check_if_won(self, results: dict, runner_number: int) -> bool:
        """Check if runner won"""
        # Implementation depends on API response structure
        return results.get("winner") == runner_number
```

---

## Step 10: Testing

### Unit Tests

Create `tests/test_value_calculator.py`:

```python
import pytest
from value_calculator import ValueCalculator

def test_find_value_bets():
    calc = ValueCalculator(min_value_threshold=0.1)

    predictions = [
        {"runner_number": 1, "odds": 3.0, "win_probability": 0.4},  # Value
        {"runner_number": 2, "odds": 2.0, "win_probability": 0.3},  # No value
    ]

    value_bets = calc.find_value_bets(predictions)

    assert len(value_bets) == 1
    assert value_bets[0]["runner_number"] == 1
    assert value_bets[0]["has_value"] == True

def test_kelly_criterion():
    calc = ValueCalculator()

    stake = calc.calculate_optimal_stake(
        bankroll=1000,
        odds=3.0,
        win_probability=0.4,
        max_bet_pct=0.02
    )

    assert stake > 0
    assert stake <= 20  # 2% of 1000
```

Run tests:
```bash
pytest tests/
```

---

## Conclusion

Congratulations! You've built a complete betting bot with:

✅ **Form Analysis** - Statistical runner evaluation  
✅ **Value Detection** - Expected value calculations  
✅ **Risk Management** - Kelly Criterion + limits  
✅ **Data Tracking** - SQLite database  
✅ **Performance Analytics** - ROI, win rate, P/L  

### Next Steps

1. **Backtest** the bot on historical data
2. **Tune parameters** (thresholds, weights)
3. **Add machine learning** for better predictions
4. **Implement live betting** (requires password grant)
5. **Add notifications** (email, SMS, Discord)
6. **Build dashboard** (web UI with charts)

### Important Warnings

⚠️ **This is for educational purposes only**  
⚠️ **Betting involves real money risk**  
⚠️ **Never bet more than you can afford to lose**  
⚠️ **Past performance doesn't guarantee future results**  
⚠️ **Responsible gambling - know when to stop**  

---

**Ready for more?** Check out:
- [Racing Form Analysis Tutorial](TUTORIAL_FORM_ANALYSIS.md)
- [Sports Odds Comparison Tutorial](TUTORIAL_ODDS_COMPARISON.md)

**Need help?** [Open an issue](https://github.com/bencousins22/tab-mcp/issues)
