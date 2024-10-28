import drafter

components, others = [], []
for field in dir(drafter):
    if field.startswith("__"):
        continue
    value = getattr(drafter, field)
    # Check if value is a class
    if hasattr(value, "__bases__") and issubclass(value, drafter.components.PageContent):
        components.append(field)
    else:
        others.append(field)


print("Components:")
print(components)
print()
print("Others:")
print(others)