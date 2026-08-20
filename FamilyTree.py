import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from datetime import datetime


# ============================================================
# 1. FILE
# ============================================================

file_path = r"C:\Users\basil\Desktop\Base\Other\Datasets\Family tree\FamilyTree.xlsx"

df = pd.read_excel(file_path)


# ============================================================
# 2. CLEAN COLUMN NAMES / VALUES
# ============================================================

df.columns = df.columns.str.strip()


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
# 3. BUILD FAMILY UNITS
# ============================================================
#
# Every FamilyID represents one couple/family.
#
# Example:
#
# FAM-001 -> Moquim + Fahmida
# FAM-002 -> Rizwan + Nikhat
# FAM-003 -> Irfan + Noor
#
# ============================================================

families = {}

for _, row in df.iterrows():

    family_id = row["FamilyID"]

    if not family_id:
        continue

    name = row["Name"]
    gender = row["Gender"].upper()
    spouse = row["Spouse"]

    # Ignore self-spouses like:
    # Basil-Basil
    if spouse == name:
        spouse = ""

    # --------------------------------------------------------
    # First occurrence of a FamilyID wins.
    # Prevents duplicate FamilyID records.
    # --------------------------------------------------------

    if family_id not in families:

        families[family_id] = {
            "id": family_id,

            "name": name,
            "gender": gender,

            "spouse": spouse,
            "spouse_gender": "",

            "father": row["Father"],
            "mother": row["Mother"],

            "generation": row["Generation"],
            "birth": row["Birth"]
        }


# ============================================================
# 4. DETERMINE GENDER OF PEOPLE
# ============================================================

known_gender = {}

for family in families.values():

    if family["name"] and family["gender"] in {"M", "F"}:
        known_gender[family["name"]] = family["gender"]


# Infer spouse gender where possible
for family in families.values():

    spouse = family["spouse"]

    if not spouse:
        continue

    # Already known from another record
    if spouse in known_gender:

        family["spouse_gender"] = known_gender[spouse]

    # Infer from primary person's gender
    elif family["gender"] == "M":

        family["spouse_gender"] = "F"

    elif family["gender"] == "F":

        family["spouse_gender"] = "M"

    else:

        family["spouse_gender"] = ""


# ============================================================
# 5. FAMILY MEMBERS
# ============================================================

for family in families.values():

    family["members"] = [
        {
            "name": family["name"],
            "gender": family["gender"]
        }
    ]

    if family["spouse"]:

        family["members"].append({
            "name": family["spouse"],
            "gender": family["spouse_gender"]
        })


# ============================================================
# 6. FIND PARENT FAMILY
# ============================================================
#
# IMPORTANT:
# The family itself MUST be excluded from the search.
#
# This fixes the FAM-001 -> FAM-001 self-parent problem.
# ============================================================

def find_parent_family(
    child_family_id,
    child_family
):

    father = child_family["father"]
    mother = child_family["mother"]

    if not father and not mother:
        return None

    for family_id, family in families.items():

        # ----------------------------------------------------
        # CRITICAL FIX
        # ----------------------------------------------------

        if family_id == child_family_id:
            continue

        member_names = {
            member["name"]
            for member in family["members"]
        }

        # Both parents known
        if father and mother:

            if (
                father in member_names
                and
                mother in member_names
            ):
                return family_id

        # Only father known
        elif father:

            if father in member_names:
                return family_id

        # Only mother known
        elif mother:

            if mother in member_names:
                return family_id

    return None


# ============================================================
# 7. BUILD PARENT -> CHILD RELATIONSHIPS
# ============================================================

children = {
    family_id: []
    for family_id in families
}

parent_of = {}

for family_id, family in families.items():

    parent_family = find_parent_family(
        family_id,
        family
    )

    parent_of[family_id] = parent_family

    if parent_family is not None:

        children[parent_family].append(
            family_id
        )


# ============================================================
# 8. SORT CHILDREN BY BIRTH DATE
# ============================================================

def birth_date(family):

    try:

        date = pd.to_datetime(
            family["birth"],
            errors="coerce"
        )

        if pd.isna(date):
            return datetime.max

        return date.to_pydatetime()

    except Exception:

        return datetime.max


for family_id in children:

    children[family_id].sort(
        key=lambda child_id:
        birth_date(families[child_id])
    )


# ============================================================
# 9. IDENTIFY ROOT FAMILIES
# ============================================================

roots = [
    family_id
    for family_id, parent_id in parent_of.items()
    if parent_id is None
]


print()
print("Root families:")
for root in roots:
    print(
        root,
        "->",
        families[root]["name"],
        "+",
        families[root]["spouse"]
    )


# ============================================================
# 10. GENERATION NUMBERS
# ============================================================

def get_generation(family):

    try:
        return int(
            float(
                family["generation"]
            )
        )

    except Exception:

        return None


generations = sorted({
    get_generation(family)
    for family in families.values()
    if get_generation(family) is not None
})


print()
print("Generations found:", generations)


# ============================================================
# 11. CALCULATE FAMILY WIDTH
# ============================================================

leaf_count = {}


def calculate_leaf_count(family_id):

    if family_id in leaf_count:
        return leaf_count[family_id]

    family_children = children.get(
        family_id,
        []
    )

    if not family_children:

        leaf_count[family_id] = 1

        return 1

    total = 0

    for child_id in family_children:

        total += calculate_leaf_count(
            child_id
        )

    leaf_count[family_id] = total

    return total


for root in roots:
    calculate_leaf_count(root)


# ============================================================
# 12. CALCULATE FAMILY X POSITIONS
# ============================================================
#
# Every family gets a horizontal slot.
#
# Children are positioned first.
# Parent is then centered above its children.
# ============================================================

family_x = {}

X_SPACING = 5


def assign_positions(
    family_id,
    left_x
):

    family_children = children.get(
        family_id,
        []
    )

    # --------------------------------------------------------
    # No children
    # --------------------------------------------------------

    if not family_children:

        family_x[family_id] = left_x

        return left_x + X_SPACING


    # --------------------------------------------------------
    # Position children first
    # --------------------------------------------------------

    child_positions = []

    current_x = left_x

    for child_id in family_children:

        current_x = assign_positions(
            child_id,
            current_x
        )

        child_positions.append(
            family_x[child_id]
        )


    # --------------------------------------------------------
    # Parent centered over children
    # --------------------------------------------------------

    family_x[family_id] = (
        min(child_positions)
        +
        max(child_positions)
    ) / 2

    return current_x


# Position each independent root branch
current_x = 0

for root in roots:

    current_x = assign_positions(
        root,
        current_x
    )

    current_x += 5


# ============================================================
# 13. FALLBACK FOR ANY UNPOSITIONED FAMILIES
# ============================================================
#
# This prevents another KeyError if the data contains a
# disconnected or unusual branch.
# ============================================================

for family_id in families:

    if family_id not in family_x:

        family_x[family_id] = current_x

        current_x += X_SPACING


# ============================================================
# 14. GENERATION Y POSITIONS
# ============================================================

GENERATION_GAP = 5.0

generation_y = {}

for index, generation in enumerate(generations):

    generation_y[generation] = (
        -index * GENERATION_GAP
    )


# ============================================================
# 15. DRAW SETTINGS
# ============================================================

fig, ax = plt.subplots(
    figsize=(28, 18)
)


# ============================================================
# 16. COLORS
# ============================================================

MALE_FILL = "#B9DDF5"
MALE_EDGE = "#5B9BD5"

FEMALE_FILL = "#F4C2D7"
FEMALE_EDGE = "#D889A8"

UNKNOWN_FILL = "#EEEEEE"
UNKNOWN_EDGE = "#888888"

LINE_COLOR = "#777777"


BOX_WIDTH = 2.2
BOX_HEIGHT = 0.65

SPOUSE_GAP = 0.20


# ============================================================
# 17. DRAW PERSON
# ============================================================

def draw_person(
    x,
    y,
    name,
    gender
):

    if gender == "M":

        fill = MALE_FILL
        edge = MALE_EDGE

    elif gender == "F":

        fill = FEMALE_FILL
        edge = FEMALE_EDGE

    else:

        fill = UNKNOWN_FILL
        edge = UNKNOWN_EDGE

    box = FancyBboxPatch(
        (
            x - BOX_WIDTH / 2,
            y - BOX_HEIGHT / 2
        ),

        BOX_WIDTH,
        BOX_HEIGHT,

        boxstyle="round,pad=0.04,rounding_size=0.08",

        linewidth=1.2,

        facecolor=fill,
        edgecolor=edge
    )

    ax.add_patch(box)

    ax.text(
        x,
        y,
        name,

        ha="center",
        va="center",

        fontsize=4,

        color="#222222"
    )


# ============================================================
# 18. DRAW FAMILY / COUPLE
# ============================================================

def draw_family(family_id):

    family = families[family_id]

    x = family_x[family_id]

    generation = get_generation(
        family
    )

    y = generation_y[generation]

    members = family["members"]


    # --------------------------------------------------------
    # SINGLE PERSON
    # --------------------------------------------------------

    if len(members) == 1:

        draw_person(
            x,
            y,
            members[0]["name"],
            members[0]["gender"]
        )

        return


    # --------------------------------------------------------
    # COUPLE
    # --------------------------------------------------------

    left_x = (
        x
        -
        (BOX_WIDTH + SPOUSE_GAP) / 2
    )

    right_x = (
        x
        +
        (BOX_WIDTH + SPOUSE_GAP) / 2
    )


    draw_person(
        left_x,
        y,
        members[0]["name"],
        members[0]["gender"]
    )


    draw_person(
        right_x,
        y,
        members[1]["name"],
        members[1]["gender"]
    )


    # Marriage line

    ax.plot(
        [
            left_x + BOX_WIDTH / 2,
            right_x - BOX_WIDTH / 2
        ],

        [
            y,
            y
        ],

        color=LINE_COLOR,

        linewidth=1.4
    )


# ============================================================
# 19. DRAW FAMILY CONNECTIONS
# ============================================================

for parent_id, child_ids in children.items():

    if not child_ids:
        continue

    parent_family = families[parent_id]

    parent_x = family_x[parent_id]

    parent_y = generation_y[
        get_generation(parent_family)
    ]


    child_positions = []

    for child_id in child_ids:

        child_family = families[child_id]

        child_x = family_x[child_id]

        child_y = generation_y[
            get_generation(child_family)
        ]

        child_positions.append(
            (child_x, child_y)
        )


    # --------------------------------------------------------
    # Parent connection starts under parent family
    # --------------------------------------------------------

    start_y = (
        parent_y
        -
        BOX_HEIGHT / 2
    )


    # --------------------------------------------------------
    # Midpoint between parent and children
    # --------------------------------------------------------

    child_y_values = [
        y
        for _, y in child_positions
    ]

    lower_generation_y = min(
        child_y_values
    )

    middle_y = (
        start_y
        +
        lower_generation_y
        +
        BOX_HEIGHT / 2
    ) / 2


    # --------------------------------------------------------
    # Vertical line from parent
    # --------------------------------------------------------

    ax.plot(
        [
            parent_x,
            parent_x
        ],

        [
            start_y,
            middle_y
        ],

        color=LINE_COLOR,
        linewidth=1.2
    )


    # --------------------------------------------------------
    # Horizontal sibling branch
    # --------------------------------------------------------

    if len(child_positions) > 1:

        xs = [
            x
            for x, _ in child_positions
        ]

        ax.plot(
            [
                min(xs),
                max(xs)
            ],

            [
                middle_y,
                middle_y
            ],

            color=LINE_COLOR,
            linewidth=1.2
        )


    # --------------------------------------------------------
    # Vertical connection to every child
    # --------------------------------------------------------

    for child_x, child_y in child_positions:

        ax.plot(
            [
                child_x,
                child_x
            ],

            [
                middle_y,
                child_y + BOX_HEIGHT / 2
            ],

            color=LINE_COLOR,
            linewidth=1.2
        )


# ============================================================
# 20. DRAW FAMILIES
# ============================================================

for generation in generations:

    generation_families = [
        family_id

        for family_id, family
        in families.items()

        if get_generation(family)
        == generation
    ]

    generation_families.sort(
        key=lambda family_id:
        family_x[family_id]
    )

    for family_id in generation_families:

        draw_family(
            family_id
        )


# ============================================================
# 21. GENERATION LABELS
# ============================================================

left_edge = min(
    family_x.values()
)

label_x = left_edge - 4


for generation in generations:

    y = generation_y[generation]

    ax.text(
        label_x,
        y,

        f"Generation {generation}",

        ha="right",
        va="center",

        fontsize=12,
        fontweight="bold",

        color="#444444"
    )


# ============================================================
# 22. OPTIONAL TITLE
# ============================================================

ax.text(
    0.5,
    1.02,

    "Family Tree",

    transform=ax.transAxes,

    ha="center",
    va="bottom",

    fontsize=18,
    fontweight="bold",

    color="#222222"
)


# ============================================================
# 23. FINAL LAYOUT
# ============================================================

ax.axis("off")

ax.set_aspect(
    "equal",
    adjustable="datalim"
)

all_x = list(
    family_x.values()
)

all_y = list(
    generation_y.values()
)

ax.set_xlim(
    min(all_x) - 5,
    max(all_x) + 5
)

ax.set_ylim(
    min(all_y) - 3,
    max(all_y) + 3
)

plt.tight_layout()


# ============================================================
# 24. SAVE
# ============================================================

output_file = r"C:\Users\basil\Desktop\Base\Other\Datasets\Family tree\FamilyTree.pdf"

plt.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight",
    facecolor="white"
)

plt.show()


# ============================================================
# 25. SUMMARY
# ============================================================

print()
print("==========================================")
print(" FAMILY TREE CREATED SUCCESSFULLY")
print("==========================================")
print()

print("Generations:", generations)
print("Root families:", roots)
print("Total family units:", len(families))

print()
print("Saved to:")
print(output_file)