def get_size_requirement_str(size_requirements, bolded: bool = True) -> str:
    formatted_sizes = map(lambda size: f"**{size.upper()}**" if bolded else size.upper(), size_requirements)
    return ", ".join(formatted_sizes)