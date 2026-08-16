import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# 1. LOAD DATA
# ============================================================

file_path = r"C:\Users\basil\Desktop\Base\Other\Datasets\Family tree\FamilyTree.xlsx"

df = pd.read_excel(file_path)

# Clean column names
df.columns = df.columns.str.strip()


# ============================================================
# 2. CLEAN DATA
# ============================================================

def clean(value):
    if pd.isna(value):
        return ""

    value = str(value).strip()

    if value.lower() in {
        "",
        "nan",
        "none",
        "n/a",
        "#n/a"
    }:
        return ""

    return value


for col in df.columns:
    df[col] = df[col].apply(clean)

# ============================================================
# 3. CLEAN GENERATION / GENDER
# ============================================================

df["Generation_num"] = pd.to_numeric(
    df["Generation"],
    errors="coerce"
)

# Sorted list of available generations
generations = sorted(
    df["Generation_num"]
    .dropna()
    .unique()
    .astype(int)
)

df["Gender"] = df["Gender"].str.upper()

df["Name"] = df["Name"].str.strip()

df["Spouse"] = df["Spouse"].str.strip()


# ============================================================
# 4. CONVERT DATES
# ============================================================

df["BirthDate"] = pd.to_datetime(
    df["Birth"],
    errors="coerce"
)

df["SpouseBirthDate"] = pd.to_datetime(
    df["Spouse birth"],
    errors="coerce"
)


# ============================================================
# 5. MARRIAGE FLAG
# ============================================================
#
# A person is considered married if a valid spouse is recorded.
#
# Excludes:
#   blank
#   #N/A
#   same person
#
# ============================================================

df["Married"] = (
    df["Spouse"].ne("")
    &
    df["Spouse"].ne(df["Name"])
)


# ============================================================
# 6. CURRENT AGE
# ============================================================

today = pd.Timestamp.today()

df["Age_calculated"] = np.nan

valid_birth = df["BirthDate"].notna()

df.loc[valid_birth, "Age_calculated"] = (
    (today - df.loc[valid_birth, "BirthDate"]).dt.days
    / 365.2425
).round(2)


# ============================================================
# 7. AGE GAP
# ============================================================
#
# Calculates age difference between person and spouse
# when both birth dates are available.
#
# ============================================================

df["AgeGap_calculated"] = np.nan

valid_spouse_birth = (
    df["BirthDate"].notna()
    &
    df["SpouseBirthDate"].notna()
)

df.loc[valid_spouse_birth, "AgeGap_calculated"] = (
    (
        df.loc[valid_spouse_birth, "BirthDate"]
        -
        df.loc[valid_spouse_birth, "SpouseBirthDate"]
    )
    .dt.days
    .abs()
    / 365.2425
).round(2)


# ============================================================
# 8. BASIC OVERVIEW
# ============================================================

print("\n")
print("=" * 70)
print("FAMILY TREE EDA")
print("=" * 70)

print(f"\nTotal records: {len(df)}")

print(
    f"Total people with names: "
    f"{df['Name'].ne('').sum()}"
)

print(
    f"Unique people names: "
    f"{df.loc[df['Name'].ne(''), 'Name'].nunique()}"
)

print(
    f"People with recorded spouses: "
    f"{df['Married'].sum()}"
)

print(
    f"People without recorded spouses: "
    f"{(~df['Married']).sum()}"
)


# ============================================================
# 9. PEOPLE BY GENERATION
# ============================================================

people_by_generation = (
    df[df["Generation_num"].notna()]
    .groupby("Generation_num")
    .size()
    .reset_index(name="People")
)

print("\n")
print("=" * 70)
print("PEOPLE BY GENERATION")
print("=" * 70)

print(
    people_by_generation.to_string(
        index=False
    )
)


# ============================================================
# 10. MALES AND FEMALES BY GENERATION
# ============================================================

gender_generation = pd.crosstab(
    df["Generation_num"],
    df["Gender"]
)

# Keep only M/F where available
for gender in ["M", "F"]:
    if gender not in gender_generation.columns:
        gender_generation[gender] = 0

gender_generation = gender_generation[
    ["M", "F"]
].fillna(0).astype(int)

gender_generation["Total"] = (
    gender_generation["M"]
    +
    gender_generation["F"]
)

gender_generation["Male %"] = (
    gender_generation["M"]
    /
    gender_generation["Total"]
    *
    100
).round(1)

gender_generation["Female %"] = (
    gender_generation["F"]
    /
    gender_generation["Total"]
    *
    100
).round(1)


print("\n")
print("=" * 70)
print("MALES AND FEMALES BY GENERATION")
print("=" * 70)

print(
    gender_generation.to_string()
)


# ============================================================
# 11. MARRIAGE BY GENERATION
# ============================================================

marriage_generation = (
    df[df["Generation_num"].notna()]
    .groupby("Generation_num")
    .agg(
        Total_people=("Name", "count"),
        Married=("Married", "sum")
    )
)

marriage_generation["Unmarried"] = (
    marriage_generation["Total_people"]
    -
    marriage_generation["Married"]
)

marriage_generation["Marriage_rate_%"] = (
    marriage_generation["Married"]
    /
    marriage_generation["Total_people"]
    *
    100
).round(1)


print("\n")
print("=" * 70)
print("MARRIAGE BY GENERATION")
print("=" * 70)

print(
    marriage_generation.to_string()
)


# ============================================================
# 12. MARRIAGE BY GENDER AND GENERATION
# ============================================================

marriage_gender_generation = (
    df[df["Generation_num"].notna()]
    .groupby(
        ["Generation_num", "Gender"]
    )
    .agg(
        People=("Name", "count"),
        Married=("Married", "sum")
    )
)

marriage_gender_generation["Unmarried"] = (
    marriage_gender_generation["People"]
    -
    marriage_gender_generation["Married"]
)

marriage_gender_generation["Marriage_rate_%"] = (
    marriage_gender_generation["Married"]
    /
    marriage_gender_generation["People"]
    *
    100
).round(1)


print("\n")
print("=" * 70)
print("MARRIAGE BY GENDER AND GENERATION")
print("=" * 70)

print(
    marriage_gender_generation.to_string()
)


# ============================================================
# 13. NUMBER OF COUPLES BY GENERATION
# ============================================================
#
# Since each married row represents one couple in your
# dataset, we count unique FamilyIDs with a spouse.
#
# ============================================================

couples_by_generation = (
    df[df["Married"]]
    .groupby("Generation_num")["FamilyID"]
    .nunique()
    .rename("Couples")
)

print("\n")
print("=" * 70)
print("COUPLES BY GENERATION")
print("=" * 70)

print(
    couples_by_generation.to_string()
)


# ============================================================
# 14. AGE AT MARRIAGE
# ============================================================
#
# Your data doesn't contain a marriage date, so we cannot
# calculate actual age at marriage.
#
# We CAN analyse:
#
#   person's current age
#   spouse age
#   age gap
#
# ============================================================

married_with_age = df[
    df["Married"]
    &
    df["Age_calculated"].notna()
]

if len(married_with_age) > 0:

    print("\n")
    print("=" * 70)
    print("AGE OF MARRIED PEOPLE")
    print("=" * 70)

    print(
        married_with_age[
            "Age_calculated"
        ].describe().round(2)
    )


# ============================================================
# 15. AGE GAP
# ============================================================

age_gap_data = df[
    df["Married"]
    &
    df["AgeGap_calculated"].notna()
]

if len(age_gap_data) > 0:

    print("\n")
    print("=" * 70)
    print("SPOUSAL AGE GAP")
    print("=" * 70)

    print(
        age_gap_data[
            "AgeGap_calculated"
        ].describe().round(2)
    )


# ============================================================
# 16. AGE GAP BY GENERATION
# ============================================================

age_gap_generation = (
    df[
        df["Married"]
        &
        df["AgeGap_calculated"].notna()
    ]
    .groupby("Generation_num")
    ["AgeGap_calculated"]
    .agg(
        Average="mean",
        Median="median",
        Minimum="min",
        Maximum="max"
    )
    .round(2)
)

print("\n")
print("=" * 70)
print("SPOUSAL AGE GAP BY GENERATION")
print("=" * 70)

print(
    age_gap_generation.to_string()
)


# ============================================================
# 17. CHILDREN PER FAMILY
# ============================================================
#
# Number of children attached to each family based on
# Father / Mother information.
#
# ============================================================

family_children = {}

for family_id in df["FamilyID"].unique():

    if not family_id:
        continue

    family_children[family_id] = 0


for _, row in df.iterrows():

    father = row["Father"]
    mother = row["Mother"]

    if not father and not mother:
        continue

    # Find family containing these parents
    parent_family = None

    for _, parent_row in df.iterrows():

        parent_name = parent_row["Name"]
        parent_spouse = parent_row["Spouse"]

        if (
            father
            and mother
            and (
                (
                    parent_name == father
                    and
                    parent_spouse == mother
                )
                or
                (
                    parent_name == mother
                    and
                    parent_spouse == father
                )
            )
        ):
            parent_family = parent_row["FamilyID"]
            break

    if parent_family in family_children:

        family_children[parent_family] += 1


# Convert to DataFrame
children_df = pd.DataFrame(
    list(
        family_children.items()
    ),
    columns=[
        "FamilyID",
        "Children"
    ]
)


# Add generation
children_df = children_df.merge(
    df[
        [
            "FamilyID",
            "Generation_num"
        ]
    ].drop_duplicates("FamilyID"),
    on="FamilyID",
    how="left"
)


print("\n")
print("=" * 70)
print("CHILDREN PER FAMILY")
print("=" * 70)

print(
    children_df[
        "Children"
    ].describe().round(2)
)


# ============================================================
# 18. LARGEST FAMILIES
# ============================================================

largest_families = (
    children_df
    .sort_values(
        "Children",
        ascending=False
    )
    .head(10)
    .merge(
        df[
            [
                "FamilyID",
                "Name",
                "Spouse"
            ]
        ].drop_duplicates("FamilyID"),
        on="FamilyID",
        how="left"
    )
)

print("\n")
print("=" * 70)
print("TOP 10 FAMILIES BY NUMBER OF CHILDREN")
print("=" * 70)

print(
    largest_families[
        [
            "FamilyID",
            "Name",
            "Spouse",
            "Children"
        ]
    ].to_string(index=False)
)


# ============================================================
# 19. BIRTHS BY YEAR
# ============================================================

birth_years = (
    df[
        df["BirthDate"].notna()
    ]["BirthDate"]
    .dt.year
    .value_counts()
    .sort_index()
)

print("\n")
print("=" * 70)
print("BIRTHS BY YEAR")
print("=" * 70)

print(
    birth_years.to_string()
)


# ============================================================
# 20. GENERATION BIRTH YEAR RANGE
# ============================================================

generation_birth_years = (
    df[
        df["BirthDate"].notna()
        &
        df["Generation_num"].notna()
    ]
    .assign(
        BirthYear=lambda x:
        x["BirthDate"].dt.year
    )
    .groupby("Generation_num")
    ["BirthYear"]
    .agg(
        Earliest="min",
        Latest="max"
    )
)

print("\n")
print("=" * 70)
print("BIRTH YEAR RANGE BY GENERATION")
print("=" * 70)

print(
    generation_birth_years.to_string()
)


# ============================================================
# 21. DATA QUALITY
# ============================================================

print("\n")
print("=" * 70)
print("DATA QUALITY")
print("=" * 70)

print(
    f"Missing names: "
    f"{df['Name'].eq('').sum()}"
)

print(
    f"Missing gender: "
    f"{df['Gender'].eq('').sum()}"
)

print(
    f"Missing birth dates: "
    f"{df['BirthDate'].isna().sum()}"
)

print(
    f"Missing generation: "
    f"{df['Generation_num'].isna().sum()}"
)

print(
    f"Missing spouses: "
    f"{(~df['Married']).sum()}"
)


# ============================================================
#                         CHARTS
# ============================================================

# ------------------------------------------------------------
# GLOBAL PLOT SETTINGS
# ------------------------------------------------------------

plt.rcParams.update({
    "figure.figsize": (10, 5.5),
    "font.size": 10,
    "axes.titlesize": 15,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.spines.bottom": True,
    "axes.titleweight": "bold",
})


# ============================================================
# COLORS
# ============================================================

MALE_COLOR = "#5B9BD5"
FEMALE_COLOR = "#E89AB5"


# ============================================================
# 1. PEOPLE BY GENERATION
# ============================================================

fig, ax = plt.subplots()

bars = ax.bar(
    people_by_generation["Generation_num"].astype(int).astype(str),
    people_by_generation["People"],
    width=0.65
)

ax.set_title("Number of People by Generation")
ax.set_xlabel("Generation")

# No Y-axis because values are displayed on bars
ax.set_ylabel("")
ax.tick_params(axis="y", left=False, labelleft=False)

ax.grid(
    axis="y",
    linestyle="--",
    alpha=0.20
)

ax.bar_label(
    bars,
    padding=4,
    fontsize=10
)

ax.set_axisbelow(True)

plt.tight_layout()
plt.show()


# ============================================================
# 2. MALE VS FEMALE BY GENERATION
# ============================================================

fig, ax = plt.subplots()

x = np.arange(
    len(gender_generation)
)

width = 0.36

male_bars = ax.bar(
    x - width / 2,
    gender_generation["M"],
    width,
    color=MALE_COLOR
)

female_bars = ax.bar(
    x + width / 2,
    gender_generation["F"],
    width,
    color=FEMALE_COLOR
)

ax.set_title("Male vs Female by Generation")
ax.set_xlabel("Generation")

# Remove Y-axis
ax.set_ylabel("")
ax.tick_params(axis="y", left=False, labelleft=False)

ax.set_xticks(x)
ax.set_xticklabels(
    gender_generation.index.astype(int)
)

ax.grid(
    axis="y",
    linestyle="--",
    alpha=0.20
)

ax.bar_label(
    male_bars,
    padding=3,
    fontsize=9
)

ax.bar_label(
    female_bars,
    padding=3,
    fontsize=9
)

ax.set_axisbelow(True)

plt.tight_layout()
plt.show()


# ============================================================
# 3. GENDER COMPOSITION (%)
# ============================================================

fig, ax = plt.subplots()

x = np.arange(
    len(gender_generation)
)

male_pct = gender_generation["Male %"].values
female_pct = gender_generation["Female %"].values

ax.bar(
    x,
    male_pct,
    width=0.65,
    color=MALE_COLOR
)

ax.bar(
    x,
    female_pct,
    bottom=male_pct,
    width=0.65,
    color=FEMALE_COLOR
)

ax.set_title("Gender Composition by Generation")
ax.set_xlabel("Generation")
ax.set_ylabel("Percentage")

ax.set_xticks(x)
ax.set_xticklabels(
    gender_generation.index.astype(int)
)

ax.set_ylim(0, 100)

ax.set_yticks(
    np.arange(0, 101, 20)
)

ax.set_yticklabels(
    [f"{v}%" for v in np.arange(0, 101, 20)]
)

ax.grid(
    axis="y",
    linestyle="--",
    alpha=0.20
)

ax.set_axisbelow(True)

plt.tight_layout()
plt.show()


# ============================================================
# 4. MARRIED VS UNMARRIED
# ============================================================

fig, ax = plt.subplots()

x = np.arange(
    len(marriage_generation)
)

married_bars = ax.bar(
    x - width / 2,
    marriage_generation["Married"],
    width
)

unmarried_bars = ax.bar(
    x + width / 2,
    marriage_generation["Unmarried"],
    width
)

ax.set_title("Married vs Unmarried by Generation")
ax.set_xlabel("Generation")

# Remove Y-axis
ax.set_ylabel("")
ax.tick_params(axis="y", left=False, labelleft=False)

ax.set_xticks(x)
ax.set_xticklabels(
    marriage_generation.index.astype(int)
)

ax.grid(
    axis="y",
    linestyle="--",
    alpha=0.20
)

ax.bar_label(
    married_bars,
    padding=3,
    fontsize=9
)

ax.bar_label(
    unmarried_bars,
    padding=3,
    fontsize=9
)

ax.set_axisbelow(True)

plt.tight_layout()
plt.show()


# ============================================================
# 5. MARRIAGE RATE
# ============================================================

fig, ax = plt.subplots()

x = marriage_generation.index.astype(int)
y = marriage_generation["Marriage_rate_%"]

ax.plot(
    x,
    y,
    marker="o",
    linewidth=2.5,
    markersize=7
)

for xi, yi in zip(x, y):

    ax.annotate(
        f"{yi:.0f}%",
        (xi, yi),
        textcoords="offset points",
        xytext=(0, 8),
        ha="center",
        fontsize=9
    )

ax.set_title("Marriage Rate by Generation")
ax.set_xlabel("Generation")
ax.set_ylabel("Marriage Rate")

ax.set_xticks(x)

ax.set_ylim(
    0,
    105
)

ax.set_yticks(
    np.arange(0, 101, 20)
)

ax.set_yticklabels(
    [f"{v}%" for v in np.arange(0, 101, 20)]
)

ax.grid(
    axis="y",
    linestyle="--",
    alpha=0.20
)

ax.set_axisbelow(True)

plt.tight_layout()
plt.show()


# ============================================================
# 6. MARRIAGE RATE BY GENDER
# ============================================================

marriage_gender_plot = (
    marriage_gender_generation
    .reset_index()
)

marriage_gender_plot = marriage_gender_plot[
    marriage_gender_plot["Gender"].isin(["M", "F"])
]

pivot_marriage_gender = (
    marriage_gender_plot
    .pivot(
        index="Generation_num",
        columns="Gender",
        values="Marriage_rate_%"
    )
)

for gender in ["M", "F"]:

    if gender not in pivot_marriage_gender.columns:
        pivot_marriage_gender[gender] = np.nan


fig, ax = plt.subplots()

x = np.arange(
    len(pivot_marriage_gender)
)

male_bars = ax.bar(
    x - width / 2,
    pivot_marriage_gender["M"],
    width,
    color=MALE_COLOR
)

female_bars = ax.bar(
    x + width / 2,
    pivot_marriage_gender["F"],
    width,
    color=FEMALE_COLOR
)

ax.set_title("Marriage Rate by Gender and Generation")
ax.set_xlabel("Generation")
ax.set_ylabel("Marriage Rate")

ax.set_xticks(x)

ax.set_xticklabels(
    pivot_marriage_gender.index.astype(int)
)

ax.set_ylim(0, 105)

ax.set_yticks(
    np.arange(0, 101, 20)
)

ax.set_yticklabels(
    [f"{v}%" for v in np.arange(0, 101, 20)]
)

ax.grid(
    axis="y",
    linestyle="--",
    alpha=0.20
)

ax.bar_label(
    male_bars,
    fmt="%.0f%%",
    padding=3,
    fontsize=8
)

ax.bar_label(
    female_bars,
    fmt="%.0f%%",
    padding=3,
    fontsize=8
)

ax.set_axisbelow(True)

plt.tight_layout()
plt.show()

# ============================================================
# 7. SPOUSAL AGE GAP
# ============================================================

if len(age_gap_data) > 0:

    age_gap_plot = []
    labels = []

    for generation in generations:

        values = (
            age_gap_data[
                age_gap_data["Generation_num"] == generation
            ]["AgeGap_calculated"]
            .dropna()
        )

        if len(values) > 0:

            age_gap_plot.append(values)
            labels.append(str(int(generation)))


    if age_gap_plot:

        fig, ax = plt.subplots()

        ax.boxplot(
            age_gap_plot,
            labels=labels,
            patch_artist=False
        )

        ax.set_title("Spousal Age Gap by Generation")
        ax.set_xlabel("Generation")
        ax.set_ylabel("Age Gap (Years)")

        ax.grid(
            axis="y",
            linestyle="--",
            alpha=0.20
        )

        ax.set_axisbelow(True)

        plt.tight_layout()
        plt.show()


# ============================================================
# 8. CHILDREN PER FAMILY
# ============================================================

# Get FamilyIDs where a spouse is recorded
married_family_ids = (
    df.loc[
        df["Married"],
        "FamilyID"
    ]
    .dropna()
    .unique()
)

# Keep only married families
married_children_df = children_df[
    children_df["FamilyID"].isin(
        married_family_ids
    )
].copy()


# Count how many married families have each
# number of children
children_counts = (
    married_children_df["Children"]
    .value_counts()
    .sort_index()
)


fig, ax = plt.subplots()

bars = ax.bar(
    children_counts.index.astype(int).astype(str),
    children_counts.values,
    width=0.65
)

ax.set_title(
    "Number of Children per Married Family"
)

ax.set_xlabel(
    "Number of Children"
)

# Remove Y-axis because values are shown on bars
ax.set_ylabel("")
ax.tick_params(
    axis="y",
    left=False,
    labelleft=False
)

ax.grid(
    axis="y",
    linestyle="--",
    alpha=0.20
)

ax.bar_label(
    bars,
    padding=4,
    fontsize=9
)

ax.set_axisbelow(True)

plt.tight_layout()
plt.show()

# ============================================================
# 9. AVERAGE CHILDREN PER FAMILY BY GENERATION
# ============================================================

avg_children_generation = (
    children_df
    .groupby("Generation_num")["Children"]
    .mean()
    .reindex(generations)
)

fig, ax = plt.subplots()

bars = ax.bar(
    avg_children_generation.index.astype(int).astype(str),
    avg_children_generation.values,
    width=0.65
)

ax.set_title("Average Number of Children per Family")
ax.set_xlabel("Generation")

# Remove Y-axis
ax.set_ylabel("")
ax.tick_params(axis="y", left=False, labelleft=False)

ax.grid(
    axis="y",
    linestyle="--",
    alpha=0.20
)

ax.bar_label(
    bars,
    fmt="%.1f",
    padding=4,
    fontsize=9
)

ax.set_axisbelow(True)

plt.tight_layout()
plt.show()


# ============================================================
# 10. BIRTHS OVER TIME
# ============================================================

fig, ax = plt.subplots(figsize=(12, 5.5))

ax.plot(
    birth_years.index,
    birth_years.values,
    marker="o",          # data points already enabled
    linewidth=2,
    markersize=6         # optionally make markers larger
)

ax.fill_between(
    birth_years.index,
    birth_years.values,
    alpha=0.10
)

ax.set_title("Number of Births Over Time")
ax.set_xlabel("Birth Year")

# Remove Y-axis
ax.set_ylabel("")
ax.tick_params(axis="y", left=False, labelleft=False)

ax.grid(
    axis="y",
    linestyle="--",
    alpha=0.20
)

if len(birth_years) > 20:
    step = max(1, len(birth_years) // 12)
    ax.set_xticks(birth_years.index[::step])

ax.set_axisbelow(True)

# ---------- ADD DATA POINT LABELS (optional) ----------
# This shows the count above each marker.
# If you don't want labels, delete this block.
for year, count in birth_years.items():
    ax.text(year, count + 0.5, str(int(count)),
            ha='center', va='bottom', fontsize=8, color='gray')
# -----------------------------------------------------

plt.tight_layout()
plt.show()


# ============================================================
# 11. CURRENT AGE DISTRIBUTION
# ============================================================

age_data = (
    df["Age_calculated"]
    .dropna()
)

if len(age_data) > 0:

    # --------------------------------------------------------
    # Create age groups
    # --------------------------------------------------------

    age_bins = [
        0,
        10,
        20,
        30,
        40,
        50,
        60,
        70,
        80,
        90,
        100,
        110
    ]

    age_labels = [
        "0–9",
        "10–19",
        "20–29",
        "30–39",
        "40–49",
        "50–59",
        "60–69",
        "70–79",
        "80–89",
        "90–99",
        "100+"
    ]

    age_groups = pd.cut(
        age_data,
        bins=age_bins,
        labels=age_labels,
        right=False
    )

    age_group_counts = (
        age_groups
        .value_counts()
        .reindex(age_labels)
        .fillna(0)
        .astype(int)
    )


    # --------------------------------------------------------
    # Plot
    # --------------------------------------------------------

    fig, ax = plt.subplots()

    bars = ax.bar(
        age_group_counts.index,
        age_group_counts.values,
        width=0.65
    )

    ax.set_title(
        "Current Age Distribution"
    )

    ax.set_xlabel(
        "Age Group"
    )

    # Remove Y-axis because values are shown on bars
    ax.set_ylabel("")

    ax.tick_params(
        axis="y",
        left=False,
        labelleft=False
    )

    ax.grid(
        axis="y",
        linestyle="--",
        alpha=0.20
    )

    ax.bar_label(
        bars,
        padding=4,
        fontsize=9
    )

    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.show()


# ============================================================
# FINAL
# ============================================================

print("\n")
print("=" * 70)
print("EDA COMPLETE")
print("=" * 70)