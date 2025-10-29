# Tutorial: Advanced Racing Form Analysis

## Overview

Master the art of racing form analysis using the Tabcorp MCP Server. This tutorial teaches you to build a sophisticated form analysis tool that:

- 📊 Aggregates comprehensive runner statistics
- 🏇 Analyzes track and distance performance
- 👔 Evaluates jockey and trainer records
- 📈 Calculates speed ratings and class assessments
- 🎯 Generates data-driven race predictions
- 📑 Produces professional PDF form guides

**Difficulty**: Intermediate  
**Time**: 90 minutes  
**Prerequisites**: Python, pandas, basic statistics

---

## What You'll Build

A complete form analysis application featuring:

1. **Data Aggregator**: Collect all relevant form data
2. **Statistical Engine**: Calculate performance metrics
3. **Prediction Model**: Generate win probabilities
4. **Report Generator**: Create formatted output
5. **Visualization Tools**: Charts and graphs

---

## Project Setup

### Directory Structure

```
form-analyzer/
├── analyzer.py          # Main analysis engine
├── data_collector.py    # Data aggregation
├── statistics.py        # Statistical calculations
├── predictor.py         # Prediction models
├── reporter.py          # Report generation
├── config.py            # Configuration
├── requirements.txt     # Dependencies
└── output/              # Generated reports
```

### Install Dependencies

Create `requirements.txt`:

```txt
tab-mcp>=1.0.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
seaborn>=0.12.0
reportlab>=4.0.0
python-dotenv>=1.0.0
scipy>=1.11.0
```

Install:
```bash
pip install -r requirements.txt
```

---

## Step 1: Data Collector

Create `data_collector.py`:

```python
import asyncio
from typing import Dict, List, Optional
from mcp.client import Client
import pandas as pd
from datetime import datetime

class RacingDataCollector:
    """Collect comprehensive racing data for analysis"""

    def __init__(self, client: Client, access_token: str):
        self.client = client
        self.token = access_token

    async def collect_race_data(self, meeting_id: str, race_number: int) -> Dict:
        """Collect all data for a specific race"""

        print(f"📥 Collecting data for race {race_number}...")

        # Gather data from multiple endpoints
        race_details, form_guide, runners_data = await asyncio.gather(
            self._get_race_details(meeting_id, race_number),
            self._get_form_guide(meeting_id, race_number),
            self._get_all_runner_forms(meeting_id, race_number)
        )

        return {
            "race_details": race_details,
            "form_guide": form_guide,
            "runners": runners_data,
            "collected_at": datetime.now().isoformat()
        }

    async def _get_race_details(self, meeting_id: str, race_number: int) -> Dict:
        """Get basic race information"""
        return await self.client.call_tool(
            "racing_get_race",
            {
                "access_token": self.token,
                "meeting_id": meeting_id,
                "race_number": race_number,
                "fixed_odds": True
            }
        )

    async def _get_form_guide(self, meeting_id: str, race_number: int) -> Dict:
        """Get race form guide"""
        return await self.client.call_tool(
            "racing_get_race_form",
            {
                "access_token": self.token,
                "meeting_id": meeting_id,
                "race_number": race_number
            }
        )

    async def _get_all_runner_forms(self, meeting_id: str, race_number: int) -> List[Dict]:
        """Get detailed form for all runners"""

        # Get race to know runner count
        race = await self._get_race_details(meeting_id, race_number)
        runners = race.get("runners", [])

        # Fetch all runner forms concurrently
        tasks = [
            self._get_runner_form(meeting_id, race_number, r["runner_number"])
            for r in runners
        ]

        runner_forms = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out errors
        return [
            form for form in runner_forms
            if not isinstance(form, Exception)
        ]

    async def _get_runner_form(self, meeting_id: str, race_number: int, runner_number: int) -> Dict:
        """Get detailed form for single runner"""
        try:
            return await self.client.call_tool(
                "racing_get_runner_form",
                {
                    "access_token": self.token,
                    "meeting_id": meeting_id,
                    "race_number": race_number,
                    "runner_number": runner_number
                }
            )
        except Exception as e:
            print(f"⚠️  Could not fetch form for runner {runner_number}: {e}")
            return {"runner_number": runner_number, "error": str(e)}

    def to_dataframe(self, race_data: Dict) -> pd.DataFrame:
        """Convert race data to pandas DataFrame for analysis"""

        runners = []
        for runner in race_data["runners"]:
            if "error" in runner:
                continue

            # Flatten runner data
            runner_row = {
                "number": runner.get("runner_number"),
                "name": runner.get("name"),
                "barrier": runner.get("barrier"),
                "weight": runner.get("weight"),
                "jockey": runner.get("jockey"),
                "trainer": runner.get("trainer"),
                "age": runner.get("age"),
                "sex": runner.get("sex"),
                "sire": runner.get("sire"),
                "career_starts": runner.get("statistics", {}).get("career_starts", 0),
                "career_wins": runner.get("statistics", {}).get("wins", 0),
                "career_places": runner.get("statistics", {}).get("places", 0),
                "career_earnings": runner.get("statistics", {}).get("earnings", 0),
                "last_start_position": self._parse_last_position(runner),
                "last_5_starts": runner.get("last_5_starts", "")
            }

            runners.append(runner_row)

        df = pd.DataFrame(runners)
        return df

    def _parse_last_position(self, runner: Dict) -> int:
        """Extract last start position from form"""
        form_history = runner.get("form_history", [])
        if form_history and len(form_history) > 0:
            return form_history[0].get("position", 99)
        return 99
```

---

## Step 2: Statistical Engine

Create `statistics.py`:

```python
import pandas as pd
import numpy as np
from typing import Dict, List
from scipy import stats

class FormStatistics:
    """Calculate statistical metrics for form analysis"""

    @staticmethod
    def calculate_win_rate(df: pd.DataFrame) -> pd.Series:
        """Calculate career win percentage"""
        return (df["career_wins"] / df["career_starts"]).fillna(0)

    @staticmethod
    def calculate_place_rate(df: pd.DataFrame) -> pd.Series:
        """Calculate career place percentage (wins + places)"""
        total_places = df["career_wins"] + df["career_places"]
        return (total_places / df["career_starts"]).fillna(0)

    @staticmethod
    def calculate_earnings_per_start(df: pd.DataFrame) -> pd.Series:
        """Calculate average earnings per start"""
        return (df["career_earnings"] / df["career_starts"]).fillna(0)

    @staticmethod
    def calculate_form_score(last_5: str) -> float:
        """Convert last 5 starts to numerical score (0-1)"""
        if not last_5 or pd.isna(last_5):
            return 0.5

        # Parse positions from string like "1-2-1-3-5"
        positions = []
        for char in str(last_5).replace("-", ""):
            if char.isdigit():
                positions.append(int(char))

        if not positions:
            return 0.5

        # Weight recent starts more heavily
        weights = [0.4, 0.3, 0.2, 0.1, 0.0][:len(positions)]
        weighted_positions = sum(p * w for p, w in zip(positions, weights))

        # Convert to 0-1 scale (1st=1.0, 10th+=0.0)
        score = max(0, 1 - (weighted_positions - 1) / 9)
        return score

    @staticmethod
    def calculate_consistency_score(last_5: str) -> float:
        """Measure performance consistency (lower variance = better)"""
        if not last_5 or pd.isna(last_5):
            return 0.5

        positions = [int(c) for c in str(last_5).replace("-", "") if c.isdigit()]

        if len(positions) < 2:
            return 0.5

        # Calculate coefficient of variation
        std = np.std(positions)
        mean = np.mean(positions)

        if mean == 0:
            return 0.5

        cv = std / mean

        # Lower CV = more consistent = higher score
        consistency = max(0, 1 - (cv / 2))
        return consistency

    @staticmethod
    def calculate_class_rating(earnings: float, starts: int) -> float:
        """Rate horse class based on prize money (0-100 scale)"""
        if starts == 0:
            return 50  # Unknown

        earnings_per_start = earnings / starts

        # Logarithmic scale for earnings
        if earnings_per_start <= 0:
            return 30

        # $0 = 30, $10k = 50, $100k = 70, $1M = 90, $10M = 100
        rating = 30 + (np.log10(earnings_per_start + 1) * 15)
        return min(100, max(30, rating))

    @staticmethod
    def calculate_barrier_advantage(barrier: int, field_size: int) -> float:
        """Calculate barrier position advantage (0-1 scale)"""
        if not barrier or not field_size:
            return 0.5

        # Middle barriers (30-50% of field) slightly advantaged
        ideal_position = field_size * 0.4
        distance = abs(barrier - ideal_position)

        advantage = max(0.2, 1 - (distance / field_size))
        return advantage

    @staticmethod
    def calculate_weight_burden(weight: float, average_weight: float) -> float:
        """Calculate weight handicap effect (0-1 scale, lower is better)"""
        if not weight or not average_weight:
            return 0.5

        # Each kg above average reduces score
        weight_diff = weight - average_weight
        burden = 0.5 - (weight_diff * 0.05)  # -5% per kg

        return max(0, min(1, burden))

    @staticmethod
    def normalize_scores(df: pd.DataFrame, column: str) -> pd.Series:
        """Normalize scores to 0-1 range using min-max scaling"""
        min_val = df[column].min()
        max_val = df[column].max()

        if max_val == min_val:
            return pd.Series([0.5] * len(df))

        return (df[column] - min_val) / (max_val - min_val)
```

---

## Step 3: Prediction Model

Create `predictor.py`:

```python
import pandas as pd
import numpy as np
from typing import Dict, List
from statistics import FormStatistics

class RacePredictor:
    """Generate race predictions from form analysis"""

    def __init__(self):
        self.stats = FormStatistics()

    def predict_race(self, df: pd.DataFrame, race_details: Dict) -> pd.DataFrame:
        """Generate predictions for all runners"""

        print("🔮 Generating predictions...")

        # Calculate all component scores
        df = self._calculate_all_scores(df, race_details)

        # Calculate composite win probability
        df["win_probability"] = self._calculate_win_probability(df)

        # Normalize to sum to 1.0
        df["win_probability"] = df["win_probability"] / df["win_probability"].sum()

        # Calculate suggested odds (inverse of probability)
        df["fair_odds"] = 1 / df["win_probability"]

        # Add ranking
        df["predicted_rank"] = df["win_probability"].rank(ascending=False)

        # Sort by probability
        df = df.sort_values("win_probability", ascending=False)

        return df

    def _calculate_all_scores(self, df: pd.DataFrame, race_details: Dict) -> pd.DataFrame:
        """Calculate all component scores"""

        # Win rate
        df["win_rate"] = self.stats.calculate_win_rate(df)

        # Place rate
        df["place_rate"] = self.stats.calculate_place_rate(df)

        # Form score
        df["form_score"] = df["last_5_starts"].apply(self.stats.calculate_form_score)

        # Consistency
        df["consistency"] = df["last_5_starts"].apply(self.stats.calculate_consistency_score)

        # Class rating
        df["class_rating"] = df.apply(
            lambda row: self.stats.calculate_class_rating(
                row["career_earnings"],
                row["career_starts"]
            ),
            axis=1
        )

        # Barrier advantage
        field_size = len(df)
        df["barrier_advantage"] = df["barrier"].apply(
            lambda b: self.stats.calculate_barrier_advantage(b, field_size)
        )

        # Weight burden
        avg_weight = df["weight"].mean()
        df["weight_score"] = df["weight"].apply(
            lambda w: self.stats.calculate_weight_burden(w, avg_weight)
        )

        return df

    def _calculate_win_probability(self, df: pd.DataFrame) -> pd.Series:
        """Calculate composite win probability using weighted components"""

        # Define weights for each factor
        weights = {
            "form_score": 0.25,
            "win_rate": 0.20,
            "class_rating": 0.20,
            "consistency": 0.15,
            "barrier_advantage": 0.10,
            "weight_score": 0.10
        }

        # Normalize class rating to 0-1 scale
        df["class_norm"] = df["class_rating"] / 100

        # Calculate weighted sum
        win_prob = (
            df["form_score"] * weights["form_score"] +
            df["win_rate"] * weights["win_rate"] +
            df["class_norm"] * weights["class_rating"] +
            df["consistency"] * weights["consistency"] +
            df["barrier_advantage"] * weights["barrier_advantage"] +
            df["weight_score"] * weights["weight_score"]
        )

        return win_prob

    def identify_value_bets(self, df: pd.DataFrame, min_overlay: float = 0.1) -> pd.DataFrame:
        """Identify runners with value (predicted prob > market prob)"""

        # Assuming market odds are in df["odds"]
        if "odds" not in df.columns:
            return pd.DataFrame()

        # Calculate market implied probability
        df["market_probability"] = 1 / df["odds"]

        # Calculate overlay (our prob - market prob)
        df["overlay"] = df["win_probability"] - df["market_probability"]

        # Calculate overlay percentage
        df["overlay_pct"] = (df["overlay"] / df["market_probability"]) * 100

        # Filter for value (min 10% overlay)
        value_bets = df[df["overlay_pct"] >= (min_overlay * 100)].copy()

        return value_bets.sort_values("overlay_pct", ascending=False)
```

Continuing in next message...


---

## Step 4: Report Generator

Create `reporter.py`:

```python
import pandas as pd
from typing import Dict
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

class FormReporter:
    """Generate formatted reports and visualizations"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        import os
        os.makedirs(output_dir, exist_ok=True)

    def generate_console_report(self, df: pd.DataFrame, race_details: Dict):
        """Print formatted console report"""

        print("
" + "="*80)
        print(f"🏇 FORM ANALYSIS REPORT")
        print("="*80)

        print(f"
📍 {race_details.get('meeting_name')} - Race {race_details.get('race_number')}")
        print(f"📏 Distance: {race_details.get('distance')}m")
        print(f"💰 Prize Money: ${race_details.get('prize_money', 0):,.0f}")
        print(f"🕐 Start Time: {race_details.get('start_time')}")

        print("
" + "-"*80)
        print("TOP SELECTIONS (by predicted probability):")
        print("-"*80)

        # Display top 5
        top_5 = df.head(5)

        for idx, row in top_5.iterrows():
            print(f"
{int(row['predicted_rank'])}. #{int(row['number'])} {row['name']}")
            print(f"   Win Probability: {row['win_probability']*100:.1f}%")
            print(f"   Fair Odds: ${row['fair_odds']:.2f}")
            if 'odds' in row:
                print(f"   Market Odds: ${row['odds']:.2f}")
            print(f"   Form Score: {row['form_score']:.2f}/1.0")
            print(f"   Class Rating: {row['class_rating']:.0f}/100")
            print(f"   Jockey: {row['jockey']}")
            print(f"   Barrier: {int(row['barrier'])}")
            print(f"   Weight: {row['weight']:.1f}kg")

    def generate_detailed_table(self, df: pd.DataFrame) -> str:
        """Generate detailed comparison table"""

        from tabulate import tabulate

        # Select key columns
        table_df = df[[
            'number', 'name', 'barrier', 'weight',
            'win_probability', 'form_score', 'class_rating',
            'win_rate', 'career_starts'
        ]].copy()

        # Format columns
        table_df['win_probability'] = (table_df['win_probability'] * 100).round(1)
        table_df['form_score'] = table_df['form_score'].round(2)
        table_df['class_rating'] = table_df['class_rating'].round(0)
        table_df['win_rate'] = (table_df['win_rate'] * 100).round(1)

        # Rename columns
        table_df.columns = ['#', 'Name', 'Bar', 'Wgt', 'Win%', 'Form', 'Class', 'C.Win%', 'Starts']

        return tabulate(table_df, headers='keys', tablefmt='grid', showindex=False)

    def create_visualizations(self, df: pd.DataFrame, race_name: str):
        """Create analysis charts"""

        sns.set_style('whitegrid')
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'Form Analysis: {race_name}', fontsize=16, fontweight='bold')

        # 1. Win Probability Distribution
        ax1 = axes[0, 0]
        top_10 = df.head(10)
        ax1.barh(top_10['name'], top_10['win_probability'] * 100, color='steelblue')
        ax1.set_xlabel('Win Probability (%)')
        ax1.set_title('Top 10 - Win Probability')
        ax1.invert_yaxis()

        # 2. Component Scores Radar
        ax2 = axes[0, 1]
        top_runner = df.iloc[0]
        categories = ['Form', 'Class', 'Consistency', 'Barrier', 'Weight']
        values = [
            top_runner['form_score'],
            top_runner['class_rating'] / 100,
            top_runner['consistency'],
            top_runner['barrier_advantage'],
            top_runner['weight_score']
        ]

        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values += values[:1]
        angles += angles[:1]

        ax2 = plt.subplot(222, projection='polar')
        ax2.plot(angles, values, 'o-', linewidth=2, color='steelblue')
        ax2.fill(angles, values, alpha=0.25, color='steelblue')
        ax2.set_xticks(angles[:-1])
        ax2.set_xticklabels(categories)
        ax2.set_ylim(0, 1)
        ax2.set_title(f"Top Selection: {top_runner['name']}")
        ax2.grid(True)

        # 3. Class vs Form Scatter
        ax3 = axes[1, 0]
        scatter = ax3.scatter(
            df['form_score'],
            df['class_rating'],
            s=df['win_probability'] * 1000,
            c=df['win_probability'],
            cmap='RdYlGn',
            alpha=0.6
        )
        ax3.set_xlabel('Form Score')
        ax3.set_ylabel('Class Rating')
        ax3.set_title('Form vs Class (bubble size = win probability)')
        plt.colorbar(scatter, ax=ax3, label='Win Probability')

        # Add labels for top 3
        for idx in range(min(3, len(df))):
            row = df.iloc[idx]
            ax3.annotate(
                f"#{int(row['number'])}",
                (row['form_score'], row['class_rating']),
                fontsize=8
            )

        # 4. Barrier Position Analysis
        ax4 = axes[1, 1]
        barrier_df = df.groupby('barrier')['win_probability'].mean().sort_index()
        ax4.bar(barrier_df.index, barrier_df.values * 100, color='coral')
        ax4.set_xlabel('Barrier Position')
        ax4.set_ylabel('Average Win Probability (%)')
        ax4.set_title('Win Probability by Barrier')

        plt.tight_layout()

        # Save
        filename = f"{self.output_dir}/{race_name.replace(' ', '_')}_analysis.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"
📊 Charts saved to: {filename}")
        plt.close()

    def generate_pdf_report(self, df: pd.DataFrame, race_details: Dict, value_bets: pd.DataFrame):
        """Generate professional PDF report"""

        race_name = f"{race_details.get('meeting_name')}_R{race_details.get('race_number')}"
        filename = f"{self.output_dir}/{race_name}_FormGuide.pdf"

        doc = SimpleDocTemplate(filename, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )

        story.append(Paragraph(f"Form Guide: {race_details.get('meeting_name')}", title_style))
        story.append(Paragraph(f"Race {race_details.get('race_number')} - {race_details.get('distance')}m", styles['Heading2']))
        story.append(Spacer(1, 12))

        # Race Details
        details_data = [
            ['Prize Money:', f"${race_details.get('prize_money', 0):,.0f}"],
            ['Start Time:', race_details.get('start_time', 'TBA')],
            ['Field Size:', str(len(df))],
            ['Analysis Date:', datetime.now().strftime('%Y-%m-%d %H:%M')]
        ]

        details_table = Table(details_data, colWidths=[2*inch, 3*inch])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(details_table)
        story.append(Spacer(1, 20))

        # Top Selections
        story.append(Paragraph("Top Selections", styles['Heading2']))
        story.append(Spacer(1, 12))

        top_5 = df.head(5)
        selection_data = [['Rank', '#', 'Name', 'Win%', 'Form', 'Class', 'Jockey', 'Barrier']]

        for idx, row in top_5.iterrows():
            selection_data.append([
                str(int(row['predicted_rank'])),
                str(int(row['number'])),
                row['name'][:20],
                f"{row['win_probability']*100:.1f}%",
                f"{row['form_score']:.2f}",
                f"{row['class_rating']:.0f}",
                row['jockey'][:15],
                str(int(row['barrier']))
            ])

        selection_table = Table(selection_data)
        selection_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(selection_table)
        story.append(Spacer(1, 20))

        # Value Bets
        if len(value_bets) > 0:
            story.append(Paragraph("Value Betting Opportunities", styles['Heading2']))
            story.append(Spacer(1, 12))

            value_data = [['#', 'Name', 'Market Odds', 'Fair Odds', 'Overlay %']]

            for idx, row in value_bets.iterrows():
                value_data.append([
                    str(int(row['number'])),
                    row['name'][:25],
                    f"${row.get('odds', 0):.2f}",
                    f"${row['fair_odds']:.2f}",
                    f"{row['overlay_pct']:.1f}%"
                ])

            value_table = Table(value_data)
            value_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(value_table)

        # Build PDF
        doc.build(story)
        print(f"
📄 PDF report saved to: {filename}")
```

---

## Step 5: Main Analyzer

Create `analyzer.py`:

```python
import asyncio
from mcp.client import Client
from config import Config
from data_collector import RacingDataCollector
from predictor import RacePredictor
from reporter import FormReporter

class RacingFormAnalyzer:
    """Main form analysis orchestrator"""

    def __init__(self):
        self.config = Config()
        self.predictor = RacePredictor()
        self.reporter = FormReporter()
        self.access_token = None

    async def analyze_race(self, meeting_id: str, race_number: int):
        """Analyze a specific race"""

        print("🔍 Starting Form Analysis...")
        print("="*80)

        async with Client(Config.MCP_SERVER_URL) as client:
            # Authenticate
            await self._authenticate(client)

            # Collect data
            collector = RacingDataCollector(client, self.access_token)
            race_data = await collector.collect_race_data(meeting_id, race_number)

            # Convert to DataFrame
            df = collector.to_dataframe(race_data)

            if len(df) == 0:
                print("❌ No runner data available")
                return

            print(f"✅ Collected data for {len(df)} runners")

            # Generate predictions
            df = self.predictor.predict_race(df, race_data['race_details'])

            # Identify value bets
            value_bets = self.predictor.identify_value_bets(df, min_overlay=0.10)

            # Generate reports
            self.reporter.generate_console_report(df, race_data['race_details'])

            print("
" + self.reporter.generate_detailed_table(df))

            if len(value_bets) > 0:
                print("
" + "="*80)
                print(f"💎 Found {len(value_bets)} VALUE BETTING OPPORTUNITIES:")
                print("="*80)
                for idx, row in value_bets.iterrows():
                    print(f"  #{int(row['number'])} {row['name']}:")
                    print(f"    Market Odds: ${row['odds']:.2f} | Fair Odds: ${row['fair_odds']:.2f}")
                    print(f"    Overlay: {row['overlay_pct']:.1f}%")

            # Create visualizations
            race_name = f"{race_data['race_details'].get('meeting_name')}_R{race_number}"
            self.reporter.create_visualizations(df, race_name)

            # Generate PDF
            self.reporter.generate_pdf_report(df, race_data['race_details'], value_bets)

            print("
✅ Analysis complete!")

            return df, value_bets

    async def analyze_upcoming_races(self, count: int = 5):
        """Analyze next-to-go races"""

        async with Client(Config.MCP_SERVER_URL) as client:
            await self._authenticate(client)

            # Get upcoming races
            races = await client.call_tool(
                "racing_get_next_to_go",
                {
                    "access_token": self.access_token,
                    "count": count
                }
            )

            for race in races.get('races', []):
                print(f"
{'='*80}")
                print(f"Analyzing: {race['meeting_name']} Race {race['race_number']}")
                print(f"{'='*80}")

                try:
                    await self.analyze_race(
                        race['meeting_id'],
                        race['race_number']
                    )
                except Exception as e:
                    print(f"❌ Error analyzing race: {e}")
                    continue

                # Wait between analyses
                await asyncio.sleep(2)

    async def _authenticate(self, client: Client):
        """Authenticate with API"""
        if self.access_token:
            return

        auth_result = await client.call_tool(
            "tab_oauth_client_credentials",
            {
                "client_id": Config.CLIENT_ID,
                "client_secret": Config.CLIENT_SECRET
            }
        )

        self.access_token = auth_result["access_token"]
        print("✅ Authenticated successfully
")

if __name__ == "__main__":
    import sys

    analyzer = RacingFormAnalyzer()

    if len(sys.argv) >= 3:
        # Analyze specific race
        meeting_id = sys.argv[1]
        race_number = int(sys.argv[2])
        asyncio.run(analyzer.analyze_race(meeting_id, race_number))
    else:
        # Analyze upcoming races
        asyncio.run(analyzer.analyze_upcoming_races(count=3))
```

---

## Step 6: Usage Examples

### Analyze Specific Race

```bash
python analyzer.py MEETING_12345 7
```

### Analyze Next-to-Go Races

```bash
python analyzer.py
```

### Example Output

```
🔍 Starting Form Analysis...
============================================================
✅ Authenticated successfully

📥 Collecting data for race 7...
✅ Collected data for 14 runners
🔮 Generating predictions...

============================================================
🏇 FORM ANALYSIS REPORT
============================================================

📍 Randwick - Race 7
📏 Distance: 1600m
💰 Prize Money: $150,000
🕐 Start Time: 2024-10-29T15:30:00Z

----------------------------------------------------------------------------
TOP SELECTIONS (by predicted probability):
----------------------------------------------------------------------------

1. #5 Winx
   Win Probability: 32.5%
   Fair Odds: $3.08
   Market Odds: $2.80
   Form Score: 0.92/1.0
   Class Rating: 95/100
   Jockey: H Bowman
   Barrier: 4
   Weight: 57.0kg

2. #8 Redzel
   Win Probability: 18.2%
   Fair Odds: $5.49
   Market Odds: $6.50
   Form Score: 0.78/1.0
   Class Rating: 88/100
   Jockey: K McEvoy
   Barrier: 7
   Weight: 56.5kg

============================================================
💎 Found 2 VALUE BETTING OPPORTUNITIES:
============================================================
  #8 Redzel:
    Market Odds: $6.50 | Fair Odds: $5.49
    Overlay: 18.4%

  #12 Happy Clapper:
    Market Odds: $12.00 | Fair Odds: $9.85
    Overlay: 21.8%

📊 Charts saved to: output/Randwick_R7_analysis.png
📄 PDF report saved to: output/Randwick_R7_FormGuide.pdf

✅ Analysis complete!
```

---

## Advanced Features

### Add Historical Comparison

```python
class HistoricalComparison:
    """Compare current form to historical performance"""

    def compare_track_performance(self, runner_form: Dict, track_name: str) -> Dict:
        """Analyze performance at specific track"""

        track_starts = [
            start for start in runner_form.get('form_history', [])
            if start.get('track') == track_name
        ]

        if not track_starts:
            return {'track_familiarity': 'Unknown'}

        wins = sum(1 for s in track_starts if s.get('position') == 1)
        places = sum(1 for s in track_starts if s.get('position') <= 3)

        return {
            'track_starts': len(track_starts),
            'track_wins': wins,
            'track_places': places,
            'track_win_rate': wins / len(track_starts) if track_starts else 0,
            'track_place_rate': places / len(track_starts) if track_starts else 0
        }
```

### Add Weather Impact Analysis

```python
def analyze_weather_impact(runner_form: Dict, track_condition: str) -> float:
    """Analyze runner performance in similar track conditions"""

    # Find starts in similar conditions
    similar_starts = [
        start for start in runner_form.get('form_history', [])
        if start.get('track_condition', '').startswith(track_condition[0])
    ]

    if len(similar_starts) < 2:
        return 0.5  # Neutral if insufficient data

    # Calculate performance
    avg_position = sum(s.get('position', 99) for s in similar_starts) / len(similar_starts)

    # Convert to score
    score = max(0, 1 - (avg_position - 1) / 9)
    return score
```

---

## Conclusion

You've built a sophisticated racing form analysis tool featuring:

✅ **Comprehensive Data Collection** - Multi-source aggregation  
✅ **Statistical Analysis** - Multiple performance metrics  
✅ **Prediction Models** - Weighted probability calculations  
✅ **Value Detection** - Overlay identification  
✅ **Professional Reports** - Console, PDF, and visualizations  

### Next Steps

1. **Backtest** predictions against historical results
2. **Tune weights** in prediction model
3. **Add machine learning** (Random Forest, Neural Networks)
4. **Incorporate more factors** (jockey/trainer stats, pace analysis)
5. **Build web interface** for easier access
6. **Add real-time monitoring** of odds changes

### Improve Accuracy

- Collect more historical data
- Track prediction vs actual results
- Adjust weights based on performance
- Add track-specific models
- Incorporate pace and sectional times

---

**Ready for more?** Check out:
- [Betting Bot Tutorial](TUTORIAL_BETTING_BOT.md)
- [Sports Odds Comparison Tutorial](TUTORIAL_ODDS_COMPARISON.md)
- [API Reference](API_REFERENCE.md)

**Need help?** [Open an issue](https://github.com/bencousins22/tab-mcp/issues)

---

**Last Updated**: October 29, 2024  
**Version**: 1.0.0
