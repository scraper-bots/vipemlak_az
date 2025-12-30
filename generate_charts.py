"""
Vipemlak.az Real Estate Market Analysis
Business Intelligence Charts Generator
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re
import os

# Set style for professional business charts
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Create charts directory if not exists
os.makedirs('charts', exist_ok=True)

# Load data
df = pd.read_csv('vipemlak_listings.csv')

# =============================================================================
# DATA CLEANING AND PREPARATION
# =============================================================================

def extract_number(value):
    """Extract numeric value from string"""
    if pd.isna(value):
        return None
    match = re.search(r'[\d\s]+', str(value).replace(' ', ''))
    if match:
        return float(match.group().replace(' ', ''))
    return None

def extract_rooms(value):
    """Extract room count"""
    if pd.isna(value):
        return None
    match = re.search(r'(\d+)', str(value))
    if match:
        return int(match.group(1))
    return None

# Clean price data
df['price_numeric'] = df['price'].apply(extract_number)
df['price_per_sqm_numeric'] = df['price_per_sqm'].apply(extract_number)
df['area_numeric'] = df['area'].apply(lambda x: extract_number(str(x).replace('m²', '')))
df['rooms_numeric'] = df['rooms'].apply(extract_rooms)

# Determine if listing is for sale or rent
df['listing_type'] = df['title'].apply(
    lambda x: 'Rent' if 'Kirayə' in str(x) else 'Sale'
)

# Extract district name (clean up)
df['district_clean'] = df['district'].apply(
    lambda x: str(x).replace(' rayonu', '').replace('Bakı şəhəri ', '').strip() if pd.notna(x) else 'Unknown'
)

# Filter for valid data
df_valid = df[df['price_numeric'].notna() & (df['price_numeric'] > 0)].copy()
df_sale = df_valid[df_valid['listing_type'] == 'Sale'].copy()
df_rent = df_valid[df_valid['listing_type'] == 'Rent'].copy()

# =============================================================================
# CHART 1: Market Overview - Sale vs Rent Distribution
# =============================================================================

fig, ax = plt.subplots(figsize=(10, 6))
listing_counts = df_valid['listing_type'].value_counts()
colors = ['#2E86AB', '#A23B72']
bars = ax.bar(listing_counts.index, listing_counts.values, color=colors, edgecolor='white', linewidth=2)

for bar, count in zip(bars, listing_counts.values):
    percentage = count / len(df_valid) * 100
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
            f'{count}\n({percentage:.1f}%)', ha='center', va='bottom', fontweight='bold', fontsize=12)

ax.set_ylabel('Number of Listings')
ax.set_title('Real Estate Market Overview: Sale vs Rental Listings', fontweight='bold', pad=20)
ax.set_ylim(0, max(listing_counts.values) * 1.2)
plt.tight_layout()
plt.savefig('charts/01_market_overview.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# =============================================================================
# CHART 2: Property Distribution by District (Top 10)
# =============================================================================

fig, ax = plt.subplots(figsize=(12, 7))
district_counts = df_valid['district_clean'].value_counts().head(10)
colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(district_counts)))[::-1]
bars = ax.barh(district_counts.index[::-1], district_counts.values[::-1], color=colors)

for bar, count in zip(bars, district_counts.values[::-1]):
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
            f'{count}', ha='left', va='center', fontweight='bold')

ax.set_xlabel('Number of Listings')
ax.set_title('Top 10 Districts by Property Availability', fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('charts/02_district_distribution.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# =============================================================================
# CHART 3: Average Sale Price by District (Top 10)
# =============================================================================

fig, ax = plt.subplots(figsize=(12, 7))
district_avg_price = df_sale.groupby('district_clean')['price_numeric'].mean().sort_values(ascending=True)
district_avg_price = district_avg_price[district_avg_price.index != 'Unknown'].tail(10)

colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(district_avg_price)))
bars = ax.barh(district_avg_price.index, district_avg_price.values / 1000, color=colors)

for bar, price in zip(bars, district_avg_price.values):
    ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2,
            f'{price/1000:.0f}K AZN', ha='left', va='center', fontweight='bold', fontsize=10)

ax.set_xlabel('Average Price (Thousands AZN)')
ax.set_title('Average Property Sale Price by District', fontweight='bold', pad=20)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}K'))
plt.tight_layout()
plt.savefig('charts/03_avg_price_by_district.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# =============================================================================
# CHART 4: Price per Square Meter by District
# =============================================================================

fig, ax = plt.subplots(figsize=(12, 7))
df_sale_valid_sqm = df_sale[df_sale['price_per_sqm_numeric'].notna() & (df_sale['price_per_sqm_numeric'] > 0)]
district_price_sqm = df_sale_valid_sqm.groupby('district_clean')['price_per_sqm_numeric'].mean().sort_values(ascending=True)
district_price_sqm = district_price_sqm[district_price_sqm.index != 'Unknown'].tail(10)

colors = plt.cm.Oranges(np.linspace(0.4, 0.9, len(district_price_sqm)))
bars = ax.barh(district_price_sqm.index, district_price_sqm.values, color=colors)

for bar, price in zip(bars, district_price_sqm.values):
    ax.text(bar.get_width() + 30, bar.get_y() + bar.get_height()/2,
            f'{price:.0f} AZN/m²', ha='left', va='center', fontweight='bold', fontsize=10)

ax.set_xlabel('Price per m² (AZN)')
ax.set_title('Property Value Index: Price per Square Meter by District', fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('charts/04_price_per_sqm.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# =============================================================================
# CHART 5: Room Distribution - Market Demand
# =============================================================================

fig, ax = plt.subplots(figsize=(10, 6))
df_rooms = df_valid[df_valid['rooms_numeric'].notna() & (df_valid['rooms_numeric'] <= 6)]
room_counts = df_rooms['rooms_numeric'].value_counts().sort_index()

colors = ['#E8F4F8', '#B8D4E3', '#7FB3D3', '#4A90A4', '#2E6B7F', '#1A4A5E'][:len(room_counts)]
bars = ax.bar(room_counts.index.astype(int), room_counts.values, color=colors, edgecolor='#2E6B7F', linewidth=1.5)

for bar, count in zip(bars, room_counts.values):
    percentage = count / len(df_rooms) * 100
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
            f'{count}\n({percentage:.1f}%)', ha='center', va='bottom', fontsize=10)

ax.set_xlabel('Number of Rooms')
ax.set_ylabel('Number of Listings')
ax.set_title('Market Demand: Property Distribution by Room Count', fontweight='bold', pad=20)
ax.set_xticks(room_counts.index.astype(int))
ax.set_xticklabels([f'{int(x)} Room{"s" if x > 1 else ""}' for x in room_counts.index])
plt.tight_layout()
plt.savefig('charts/05_room_distribution.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# =============================================================================
# CHART 6: Price Segments - Market Tiers
# =============================================================================

fig, ax = plt.subplots(figsize=(12, 6))
bins = [0, 50000, 100000, 200000, 300000, 500000, float('inf')]
labels = ['Budget\n(<50K)', 'Entry\n(50-100K)', 'Mid-Range\n(100-200K)',
          'Upper-Mid\n(200-300K)', 'Premium\n(300-500K)', 'Luxury\n(>500K)']
df_sale['price_segment'] = pd.cut(df_sale['price_numeric'], bins=bins, labels=labels)
segment_counts = df_sale['price_segment'].value_counts().reindex(labels)

colors = ['#90EE90', '#98D8C8', '#7EC8E3', '#5B9BD5', '#8B5CF6', '#EC4899']
bars = ax.bar(range(len(segment_counts)), segment_counts.values, color=colors, edgecolor='white', linewidth=2)

for i, (bar, count) in enumerate(zip(bars, segment_counts.values)):
    if pd.notna(count) and count > 0:
        percentage = count / segment_counts.sum() * 100
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{int(count)}\n({percentage:.1f}%)', ha='center', va='bottom', fontsize=10)

ax.set_ylabel('Number of Properties')
ax.set_title('Market Segmentation: Property Price Tiers (Sale Listings)', fontweight='bold', pad=20)
ax.set_xticks(range(len(labels)))
ax.set_xticklabels(labels)
plt.tight_layout()
plt.savefig('charts/06_price_segments.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# =============================================================================
# CHART 7: Rental Market Analysis
# =============================================================================

fig, ax = plt.subplots(figsize=(12, 6))
rental_bins = [0, 400, 600, 800, 1000, 1500, float('inf')]
rental_labels = ['Economy\n(<400)', 'Budget\n(400-600)', 'Standard\n(600-800)',
                 'Comfort\n(800-1000)', 'Premium\n(1000-1500)', 'Luxury\n(>1500)']
df_rent['rental_segment'] = pd.cut(df_rent['price_numeric'], bins=rental_bins, labels=rental_labels)
rental_segment_counts = df_rent['rental_segment'].value_counts().reindex(rental_labels)

colors = ['#FFF3E0', '#FFE0B2', '#FFCC80', '#FFB74D', '#FFA726', '#FF9800']
bars = ax.bar(range(len(rental_segment_counts)), rental_segment_counts.fillna(0).values,
              color=colors, edgecolor='#E65100', linewidth=1.5)

for i, (bar, count) in enumerate(zip(bars, rental_segment_counts.fillna(0).values)):
    if count > 0:
        percentage = count / rental_segment_counts.sum() * 100
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{int(count)}\n({percentage:.1f}%)', ha='center', va='bottom', fontsize=10)

ax.set_ylabel('Number of Properties')
ax.set_title('Rental Market Segmentation: Monthly Rent Tiers (AZN)', fontweight='bold', pad=20)
ax.set_xticks(range(len(rental_labels)))
ax.set_xticklabels(rental_labels)
plt.tight_layout()
plt.savefig('charts/07_rental_segments.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# =============================================================================
# CHART 8: Top Real Estate Agents by Listings
# =============================================================================

fig, ax = plt.subplots(figsize=(12, 7))
df_agents = df_valid[df_valid['agent_name'].notna() & (df_valid['agent_name'] != '')]
agent_counts = df_agents['agent_name'].value_counts().head(10)

colors = plt.cm.Purples(np.linspace(0.4, 0.9, len(agent_counts)))[::-1]
bars = ax.barh(agent_counts.index[::-1], agent_counts.values[::-1], color=colors)

for bar, count in zip(bars, agent_counts.values[::-1]):
    market_share = count / len(df_agents) * 100
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
            f'{count} ({market_share:.1f}%)', ha='left', va='center', fontweight='bold', fontsize=10)

ax.set_xlabel('Number of Listings')
ax.set_title('Top 10 Real Estate Agents by Market Presence', fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('charts/08_top_agents.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# =============================================================================
# CHART 9: Property Size vs Price (Scatter with trend)
# =============================================================================

fig, ax = plt.subplots(figsize=(12, 7))
df_scatter = df_sale[(df_sale['area_numeric'].notna()) &
                      (df_sale['price_numeric'].notna()) &
                      (df_sale['area_numeric'] > 0) &
                      (df_sale['area_numeric'] < 500) &
                      (df_sale['price_numeric'] < 1000000)]

scatter = ax.scatter(df_scatter['area_numeric'], df_scatter['price_numeric'] / 1000,
                     c=df_scatter['rooms_numeric'], cmap='viridis',
                     alpha=0.6, s=50, edgecolors='white', linewidth=0.5)

# Add trend line
z = np.polyfit(df_scatter['area_numeric'], df_scatter['price_numeric'] / 1000, 1)
p = np.poly1d(z)
x_line = np.linspace(df_scatter['area_numeric'].min(), df_scatter['area_numeric'].max(), 100)
ax.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2, label=f'Trend Line')

cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('Number of Rooms')
ax.set_xlabel('Property Size (m²)')
ax.set_ylabel('Price (Thousands AZN)')
ax.set_title('Property Size vs Price Relationship', fontweight='bold', pad=20)
ax.legend()
plt.tight_layout()
plt.savefig('charts/09_size_vs_price.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# =============================================================================
# CHART 10: Average Rental Yield by District
# =============================================================================

fig, ax = plt.subplots(figsize=(12, 7))
# Calculate average rental and sale prices by district
district_rent_avg = df_rent.groupby('district_clean')['price_numeric'].mean()
district_sale_avg = df_sale.groupby('district_clean')['price_numeric'].mean()

# Calculate annual rental yield percentage
common_districts = set(district_rent_avg.index) & set(district_sale_avg.index)
common_districts.discard('Unknown')
rental_yields = {}
for district in common_districts:
    annual_rent = district_rent_avg[district] * 12
    sale_price = district_sale_avg[district]
    if sale_price > 0:
        rental_yields[district] = (annual_rent / sale_price) * 100

rental_yield_series = pd.Series(rental_yields).sort_values(ascending=True).tail(10)

colors = plt.cm.Greens(np.linspace(0.4, 0.9, len(rental_yield_series)))
bars = ax.barh(rental_yield_series.index, rental_yield_series.values, color=colors)

for bar, yield_val in zip(bars, rental_yield_series.values):
    ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
            f'{yield_val:.1f}%', ha='left', va='center', fontweight='bold', fontsize=10)

ax.set_xlabel('Annual Rental Yield (%)')
ax.set_title('Investment Opportunity: Annual Rental Yield by District', fontweight='bold', pad=20)
ax.axvline(x=rental_yield_series.mean(), color='red', linestyle='--', linewidth=2, label=f'Market Avg: {rental_yield_series.mean():.1f}%')
ax.legend()
plt.tight_layout()
plt.savefig('charts/10_rental_yield.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# =============================================================================
# CHART 11: Property Type Distribution
# =============================================================================

fig, ax = plt.subplots(figsize=(10, 6))
property_types = df_valid['property_type'].value_counts().head(5)

colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6'][:len(property_types)]
bars = ax.bar(range(len(property_types)), property_types.values, color=colors, edgecolor='white', linewidth=2)

for bar, count in zip(bars, property_types.values):
    percentage = count / len(df_valid) * 100
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
            f'{count}\n({percentage:.1f}%)', ha='center', va='bottom', fontsize=11, fontweight='bold')

ax.set_ylabel('Number of Listings')
ax.set_title('Property Type Distribution in the Market', fontweight='bold', pad=20)
ax.set_xticks(range(len(property_types)))
ax.set_xticklabels(property_types.index, rotation=0)
plt.tight_layout()
plt.savefig('charts/11_property_types.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

# =============================================================================
# GENERATE SUMMARY STATISTICS FOR README
# =============================================================================

print("\n" + "="*60)
print("BUSINESS INTELLIGENCE SUMMARY")
print("="*60)

print(f"\nTotal Listings Analyzed: {len(df_valid)}")
print(f"  - For Sale: {len(df_sale)} ({len(df_sale)/len(df_valid)*100:.1f}%)")
print(f"  - For Rent: {len(df_rent)} ({len(df_rent)/len(df_valid)*100:.1f}%)")

print(f"\nSale Market:")
print(f"  - Average Price: {df_sale['price_numeric'].mean():,.0f} AZN")
print(f"  - Median Price: {df_sale['price_numeric'].median():,.0f} AZN")
print(f"  - Price Range: {df_sale['price_numeric'].min():,.0f} - {df_sale['price_numeric'].max():,.0f} AZN")

print(f"\nRental Market:")
print(f"  - Average Monthly Rent: {df_rent['price_numeric'].mean():,.0f} AZN")
print(f"  - Median Monthly Rent: {df_rent['price_numeric'].median():,.0f} AZN")

print(f"\nMost Active Districts (by listings):")
for district, count in df_valid['district_clean'].value_counts().head(5).items():
    try:
        print(f"  - {district}: {count} listings")
    except UnicodeEncodeError:
        print(f"  - [District]: {count} listings")

print(f"\nMost Expensive Districts (avg price per sqm):")
for district, price in district_price_sqm.tail(5).items():
    try:
        print(f"  - {district}: {price:,.0f} AZN/m2")
    except UnicodeEncodeError:
        print(f"  - [District]: {price:,.0f} AZN/m2")

print(f"\nTop Agents (by listings):")
for agent, count in agent_counts.head(5).items():
    try:
        print(f"  - {agent}: {count} listings")
    except UnicodeEncodeError:
        print(f"  - [Agent]: {count} listings")

print("\n" + "="*60)
print("All charts saved to 'charts/' directory")
print("="*60)
