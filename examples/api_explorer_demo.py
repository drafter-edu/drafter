#!/usr/bin/env python3
"""
Example demonstrating the API Explorer feature.

This example creates a simple website with several routes that accept parameters,
perfect for demonstrating the API Explorer.

To see the API Explorer:
1. Run this file
2. Visit http://localhost:8080/
3. Scroll down to the Debug Information section
4. Click on "🔍 Open API Explorer"
5. Test the endpoints with different parameter values!
"""
from drafter import *
from dataclasses import dataclass

@dataclass
class UserProfile:
    """User profile with name, age, and favorite color"""
    name: str
    age: int
    favorite_color: str
    points: int

@route
def index(state: UserProfile) -> Page:
    """Welcome page showing the current user profile"""
    return Page(state, [
        Header("Welcome to the API Explorer Demo", 1),
        f"Current user: {state.name}",
        LineBreak(),
        f"Age: {state.age}",
        LineBreak(),
        f"Favorite Color: {state.favorite_color}",
        LineBreak(),
        f"Points: {state.points}",
        LineBreak(),
        LineBreak(),
        Button("Update Profile", update_profile),
        Button("Add Points", add_points),
        Button("View Stats", view_stats),
    ])

@route
def update_profile(state: UserProfile, name: str, age: int, color: str) -> Page:
    """Update the user profile with new values"""
    state.name = name
    state.age = age
    state.favorite_color = color
    return Page(state, [
        Header("Profile Updated!", 2),
        f"Name: {state.name}",
        LineBreak(),
        f"Age: {state.age}",
        LineBreak(),
        f"Favorite Color: {state.favorite_color}",
        LineBreak(),
        LineBreak(),
        Button("Back to Home", index)
    ])

@route
def add_points(state: UserProfile, amount: int) -> Page:
    """Add points to the user's account"""
    state.points += amount
    return Page(state, [
        Header("Points Added!", 2),
        f"Added {amount} points",
        LineBreak(),
        f"Total points: {state.points}",
        LineBreak(),
        LineBreak(),
        Button("Back to Home", index)
    ])

@route
def view_stats(state: UserProfile) -> Page:
    """View detailed statistics about the user"""
    years_until_100 = 100 - state.age
    return Page(state, [
        Header("User Statistics", 2),
        BulletedList([
            f"Name: {state.name}",
            f"Age: {state.age}",
            f"Favorite Color: {state.favorite_color}",
            f"Points: {state.points}",
            f"Years until 100: {years_until_100}",
        ]),
        LineBreak(),
        Button("Back to Home", index)
    ])

@route
def greet(state: UserProfile, greeting: str, times: int) -> Page:
    """Greet the user multiple times with a custom greeting"""
    greetings = [f"{greeting}, {state.name}!" for _ in range(times)]
    return Page(state, [
        Header("Custom Greeting", 2),
        BulletedList(greetings),
        LineBreak(),
        Button("Back to Home", index)
    ])

if __name__ == "__main__":
    set_site_information(
        author="Drafter Team",
        description="API Explorer Demo",
        sources="https://github.com/drafter-edu/drafter",
        planning="Demonstrating the API Explorer feature",
        links="https://drafter-edu.github.io/drafter/"
    )
    
    initial_state = UserProfile(
        name="Alice",
        age=25,
        favorite_color="blue",
        points=0
    )
    
    print("=" * 60)
    print("API EXPLORER DEMO")
    print("=" * 60)
    print()
    print("To test the API Explorer:")
    print("1. Look at the Debug Information section at the bottom")
    print("2. Click '🔍 Open API Explorer'")
    print("3. Try testing different routes with various parameters!")
    print()
    print("Available routes to test:")
    print("  - update_profile(name, age, color)")
    print("  - add_points(amount)")
    print("  - greet(greeting, times)")
    print("=" * 60)
    print()
    
    start_server(initial_state, debug=True, port=8080)
