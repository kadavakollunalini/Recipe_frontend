import gradio as gr
import requests
import random
import os

BASE_URL = "http://localhost:8000"

# ---- Surprise Me data pool ----
SURPRISE_OPTIONS = [
    ("Butter Chicken", "Indian"),
    ("Margherita Pizza", "Italian"),
    ("Pad Thai", "Thai"),
    ("Tacos", "Mexican"),
    ("Sushi Rolls", "Japanese"),
    ("Shakshuka", "Middle Eastern"),
    ("Ramen", "Japanese"),
    ("Paella", "Spanish"),
    ("Biryani", "Indian"),
    ("Falafel Wrap", "Middle Eastern"),
    ("Pasta Carbonara", "Italian"),
    ("Kung Pao Chicken", "Chinese"),
]

def get_recipe(dish, cuisine, servings):
    response = requests.post(f"{BASE_URL}/generate-recipe", json={
        "dish": dish, "cuisine": cuisine, "servings": servings
    })
    if response.status_code == 200:
        data = response.json()
        return data["recipe"], data["cooking_time"], dish, cuisine, data["recipe"]
    return "Error connecting to FastAPI", "-", dish, cuisine, ""

def surprise_me(servings):
    dish, cuisine = random.choice(SURPRISE_OPTIONS)
    recipe, cooking_time, d, c, r = get_recipe(dish, cuisine, servings)
    return dish, cuisine, recipe, cooking_time, d, c, r

def save_favorite(dish, cuisine, recipe):
    if not recipe:
        return "Generate a recipe first before saving."
    requests.post(f"{BASE_URL}/favorites/add", json={
        "dish": dish, "cuisine": cuisine, "recipe": recipe
    })
    return "Saved to favorites!"

def load_favorites():
    response = requests.get(f"{BASE_URL}/favorites")
    if response.status_code == 200:
        favorites = response.json()["favorites"]
        if not favorites:
            return "No favorites saved yet."
        text = ""
        for i, fav in enumerate(favorites):
            text += f"**{i+1}. {fav['dish']} ({fav['cuisine']})**\n{fav['recipe']}\n\n---\n\n"
        return text
    return "Error loading favorites."

def get_substitute(ingredient, dish):
    response = requests.post(f"{BASE_URL}/substitute", json={
        "ingredient": ingredient, "dish": dish
    })
    if response.status_code == 200:
        return response.json()["substitute"]
    return "Error connecting to FastAPI"

theme = gr.themes.Soft(
    primary_hue="orange",
    secondary_hue="green",
    neutral_hue="slate"
)

with gr.Blocks(theme=theme, title="Recipe Generator") as demo:
    gr.Markdown("# 🍲 Recipe Generator")

    current_dish = gr.State("")
    current_cuisine = gr.State("")
    current_recipe = gr.State("")

    with gr.Tab("Generate Recipe"):
        with gr.Row():
            dish = gr.Textbox(label="Enter a dish")
            cuisine = gr.Textbox(label="Cuisine (e.g. Indian, Italian)")
            servings = gr.Slider(1, 10, step=1, value=2, label="Servings")

        with gr.Row():
            generate_btn = gr.Button("Generate", variant="primary")
            surprise_btn = gr.Button("🎲 Surprise Me!", variant="secondary")

        cooking_time_output = gr.Textbox(label="⏱ Estimated Cooking Time", interactive=False)
        recipe_output = gr.Textbox(label="Recipe", lines=12)
        save_btn = gr.Button("⭐ Save to Favorites")
        save_status = gr.Textbox(label="", interactive=False)

        generate_btn.click(
            fn=get_recipe,
            inputs=[dish, cuisine, servings],
            outputs=[recipe_output, cooking_time_output, current_dish, current_cuisine, current_recipe]
        )

        surprise_btn.click(
            fn=surprise_me,
            inputs=[servings],
            outputs=[dish, cuisine, recipe_output, cooking_time_output, current_dish, current_cuisine, current_recipe]
        )

        save_btn.click(
            fn=save_favorite,
            inputs=[current_dish, current_cuisine, current_recipe],
            outputs=save_status
        )

    with gr.Tab("Ingredient Substitutes"):
        gr.Markdown("Don't have an ingredient? Find a substitute.")
        sub_dish = gr.Textbox(label="Dish name")
        sub_ingredient = gr.Textbox(label="Ingredient you don't have")
        sub_btn = gr.Button("Find Substitute", variant="primary")
        sub_output = gr.Textbox(label="Suggested Substitutes", lines=8)

        sub_btn.click(
            fn=get_substitute,
            inputs=[sub_ingredient, sub_dish],
            outputs=sub_output
        )

    with gr.Tab("⭐ Favorites"):
        refresh_btn = gr.Button("Refresh Favorites")
        favorites_output = gr.Markdown()

        refresh_btn.click(fn=load_favorites, outputs=favorites_output)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860))
    )
