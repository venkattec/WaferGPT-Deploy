import random


def describe_defect_types(defect_types: list) -> str:
    if not defect_types or "None" in defect_types:
        return random.choice([
            "The wafer is completely defect-free.",
            "No defects were identified on the wafer.",
            "This wafer has no detected defects."
        ])

    if len(defect_types) == 1:
        return random.choice([
            f"Only one defect type was detected: {defect_types[0].strip()}.",
            f"The wafer has a single defect type: {defect_types[0].strip()}."
        ])

    if len(defect_types) == 2:
        return random.choice([
            f"Two defect types were identified: {defect_types[0].strip()} and {defect_types[1].strip()}.",
            f"The defects found are: {defect_types[0].strip()} and {defect_types[1].strip()}."
        ])

    # Three or more defect types
    defect_list = ", ".join(defect_types[:-1]).strip()
    return random.choice([
        f"Multiple defect types were detected: {defect_list}, and {defect_types[-1].strip()}.",
        f"The wafer contains several defects, including {defect_list} and {defect_types[-1].strip()}."
    ])


def describe_defect_percentage(defective_percentage: float) -> str:
    options = []
    if defective_percentage == 0:
        options = [
            "The wafer is completely defect-free.",
            "There are no defects detected on the wafer."
        ]
    elif defective_percentage < 10:
        options = [
            f"Only a small portion of the wafer is defective, approximately {defective_percentage:.2f}%.",
            f"Minimal defects were found, covering about {defective_percentage:.2f}% of the wafer."
        ]
    elif defective_percentage < 50:
        options = [
            f"A moderate portion of the wafer is defective, around {defective_percentage:.2f}%.",
            f"The wafer has some noticeable defects, affecting {defective_percentage:.2f}% of its area."
        ]
    elif defective_percentage < 100:
        options = [
            f"A significant portion of the wafer is defective, nearly {defective_percentage:.2f}%.",
            f"The defects cover a large area, approximately {defective_percentage:.2f}% of the wafer."
        ]
    else:
        options = [
            "The wafer is completely defective.",
            "The wafer has been entirely affected by defects."
        ]

    return random.choice(options)


def describe_defect_location(vertical: str, horizontal: str) -> str:
    if not vertical and not horizontal:
        return no_defect()
    options = [
        f"The defect is in the {vertical} {horizontal} part of the wafer.",
        f"You can find the defect in the {vertical}-{horizontal} quadrant of the wafer.",
        f"The wafer defect is located at the {vertical}-{horizontal} region.",
        f"The defect has been detected in the {vertical} {horizontal} section of the wafer."
    ]
    return random.choice(options)


def no_defect():
    return random.choice([
        "The wafer is completely defect-free.",
        "No defects were identified on the wafer.",
        "This wafer has no detected defects."
    ])

# Categories of defects
categories = {
    "Line-Space Defects": ["Bridge", "Break", "Gap", "Corner_Rounding", "Sidewall_Roughness", "Overlay_Error"],
    "Contact Hole Defects": ["Missing", "Deformed", "Merging", "Collapse", "Undersized", "Oversized", "Repeating"]
}

def describe_sem_defect_types(defect) -> str:
    if "No Defect" in defect:
        return random.choice([
            "The wafer is completely defect-free.",
            "No defects were identified on the wafer.",
            "This wafer has no detected defects."
        ])

    # Only one defect type
    # defect = defect.strip()
    # Get category based on the defect
    category = get_defect_category(defect)
    
    return random.choice([
        f"One defect type was detected: {defect}, which is a {category} defect.",
        f"The wafer has a defect: {defect}, belonging to the {category} category."
    ])

def get_defect_category(defect: str) -> str:
    for category, defects in categories.items():
        if defect in defects:
            return category
    return ""  # In case defect is