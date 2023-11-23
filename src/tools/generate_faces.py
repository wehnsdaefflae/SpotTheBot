import random
import time
import openai
import requests


class Simplified:
    def reply_to_prompt(self, prompt: str, model: str = "gpt-4-turbo", max_tokens: int = 300) -> str:
        reply = ""
        while True:
            try:
                messages = [{"role": "user", "content": prompt}]
                response = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=max_tokens)
                choice, = response["choices"]
                message = choice["message"]
                reply = message["content"]
                break

            except Exception as e:
                print(e)
                time.sleep(1)
                continue

        return reply

    def save_image(self, prompt: str, target_path: str, **kwargs: any) -> None:
        response = self._client.images.generate(prompt=prompt, **kwargs)
        image_url = response.data[0].url

        response = requests.get(image_url)
        response.raise_for_status()

        with open(target_path, mode="wb") as file:
            file.write(response.content)



def pick(distributions: dict[str, float]) -> str:
    choices, probabilities = tuple(zip(*distributions.items()))
    picked, = random.choices(choices, weights=probabilities, k=1)
    return picked


def get_text(prompt: str) -> str:
    pass


def get_image(prompt: str, file_path: str) -> str:
    pass


def simple_person_description() -> str:
    ethnicity_distribution = {
        "German": 80.0,
        "Turk": 3.7,
        "Pole": 1.9,
        "Russian": 1.5,
        "Italian": 1.0,
        "African German": 1.0,
        "Arab": 0.6,
        "Romanian": 0.5,
        "Greek": 0.5
    }

    age_distribution = {
        "0-4 years": 4.3,
        "5-9 years": 4.2,
        "10-14 years": 4.6,
        "15-19 years": 4.9,
        "20-24 years": 5.2,
        "25-29 years": 5.4,
        "30-34 years": 5.6,
        "35-39 years": 5.8,
        "40-44 years": 5.9,
        "45-49 years": 6.1,
        "50-54 years": 6.2,
        "55-59 years": 6.3,
        "60-64 years": 6.4,
        "65-69 years": 6.2,
        "70-74 years": 5.9,
        "75-79 years": 5.5,
        "80-84 years": 4.9,
        "85+ years": 3.8
    }

    gender_distribution = {
        "male": 50.0,
        "female": 50.0
    }

    friendly_expressions = {
        "a gentle warm smile",
        "a playful amused chuckle",
        "an open approachable grin",
        "a supportive encouraging nod",
        "a compassionate gentle beam",
        "a friendly playful wink",
        "an empathetic head tilt",
        "a comforting reassuring look",
        "a comradely hearty laugh",
        "a positive optimistic gaze"
    }

    ethnicity_picked = pick(ethnicity_distribution)
    age_picked = pick(age_distribution)
    gender_picked = pick(gender_distribution)
    expression_picked = random.choice(tuple(friendly_expressions))

    prompt = (
        f"Create one colored, comic-style portrait of a single {gender_picked} individual from the {ethnicity_picked} "
        f"ethnic group, in the {age_picked} age range, and with {expression_picked}. The appearance of the person "
        f"should reflect their ethnic, age, and gender characteristics, including elements like skin tone, hair "
        f"texture, and age-appropriate features. The image should use vibrant colors typical of comic art, with clear "
        f"outlines and minimal shading, to highlight the person's unique blend of ethnic, age, and gender identity. "
        f"Add something that would make the person stand out in a crowd and make them easily identifiable."
    )

    return prompt


def save_images() -> None:
    simple_interface = Simplified()

    with open("inspirations.txt", mode="r") as f:
        inspirations = tuple(f.readlines())

    inspiration = random.choice(inspirations).strip()

    meta_prompt = (
        f"Provide a very detailed description of a person, such that two different people could draw a portrait of "
        f"this person according to this description and it would be obvious that they drew the same person. Make use "
        f"of age, ethnicity, apparent gender, and any peculiarities in appearance that would makes them stand out in "
        f"a crowd. Don't mention facial expression. Be concise and respond in one dense and continuous paragraph. Let "
        f"the description be inspired by your visual idea of \"{inspiration}\"."
    )

    draw_prompt = (
        "Create one colored, comic-style portrait of the above person. The image should use vibrant colors typical of "
        "comic art, with clear outlines and minimal shading, to highlight the person's unique appearance."
    )

    expression_happy = "Give them a happy facial expression."
    expression_anxious = "Give them a facial expression showing extreme paranoia and anxiety."
    expression_naive = "Give them a facial expression showing extreme naivety and gullibility."

    for i, each_inspiration in enumerate(inspirations):
        description = simple_interface.reply_to_prompt(meta_prompt)

        happy_description = (
                "```\n" +
                description.strip() + "\n" +
                "```\n\n" +
                draw_prompt + " " + expression_happy
        )
        simple_interface.save_image(happy_description, f"faces/person_{i:04d}_happy.png")

        naive_description = (
                "```\n" +
                description.strip() +
                "```\n\n" +
                draw_prompt + " " + expression_naive
        )
        simple_interface.save_image(naive_description, f"faces/person_{i:04d}_naive.png")

        paranoid_description = (
                "```\n" +
                description.strip() +
                "```\n\n" +
                draw_prompt + " " + expression_anxious
        )
        simple_interface.save_image(paranoid_description, f"faces/person_{i:04d}_anxious.png")

    """
    generate 100 descriptions (be inspired by )
    generate 100 neutral portraits
    modify 100 descriptions to show gullibility / naivety
    generate 100 portraits for gullibility / naivety
    modify 100 descriptions to show paranoia / anxiety
    generate 100 portraits for paranoia / anxiety
    .04 * 3 * 100 = 12
    """


def main() -> None:
    save_images()


if __name__ == "__main__":
    main()
