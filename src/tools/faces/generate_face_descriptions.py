import json
import os
import random
import time
import openai
import requests


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


class Simplified:

    def __init__(self) -> None:
        with open("config.json", mode="r") as f:
            config = json.load(f)

        api_key = config.pop("key")
        self._client = openai.Client(api_key=api_key)
        self._text_kwargs = config.pop("text")
        self._image_kwargs = config.pop("image")

    def reply_to_prompt(self, prompt: str, **kwargs: any) -> str:
        text_kwargs = dict(self._text_kwargs)
        text_kwargs.update(kwargs)
        reply = ""

        while True:
            try:
                messages = [{"role": "user", "content": prompt}]
                completion = self._client.chat.completions.create(messages=messages, **text_kwargs)
                choice, = completion.choices
                message = choice.message
                reply = message.content
                break

            except Exception as e:
                print("Text generation failed:\n")
                print(f"PROMPT:\n{prompt}\n")
                print(f"RESPONSE:\n{e}\n")
                print("retrying...")
                time.sleep(1)
                continue

        return reply.strip()

    def save_image(self, prompt: str, target_path: str, **kwargs: any) -> None:
        image_kwargs = dict(self._image_kwargs)
        image_kwargs.update(kwargs)

        while True:
            try:
                response = self._client.images.generate(prompt=prompt, **image_kwargs)
                image_url = response.data[0].url

                response = requests.get(image_url)
                response.raise_for_status()

                with open(target_path, mode="wb") as file:
                    file.write(response.content)

                break

            except Exception as e:
                print("Image generation failed:\n")
                print(f"PROMPT:\n{prompt}\n")
                print(f"RESPONSE:\n{e}\n")
                print("retrying...")
                time.sleep(1)
                continue


def pick(distributions: dict[str, float]) -> str:
    choices, probabilities = tuple(zip(*distributions.items()))
    picked, = random.choices(choices, weights=probabilities, k=1)
    return picked

def simple_person_description() -> str:
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


def save_images(max_number: int = -1) -> None:
    simple_interface = Simplified()

    with open("inspirations.txt", mode="r") as f:
        inspirations = tuple(each_word.strip() for each_word in f.readlines())

    description_happy = (
        "Their face is illuminated with pure ecstasy, their eyes are sparkling with absolute joy. Their lips are "
        "stretched into a wide, infectious grin revealing gleaming teeth, while their rosy cheeks lift higher, "
        "radiating an unparalleled aura of pure euphoria."
    )
    description_anxious = (
        "Their eyes dart fervently, reflecting a tempest of irrational fear, their wide pupils swallowed by a vast "
        "void of unease and suspicion. Entrenched lines of worry carve gnarled paths across their pallid face, a "
        "chilling canvas punctuated by taut lips locked in a silent scream of incessant dread."
    )
    description_naive = (
        "Her wide, glistening eyes seemed perpetually stuck in a child-like state of awe, absorbing every morsel of "
        "information as indisputable truth. With lips slightly parted, and eyebrows forever pitched in surprise, "
        "the innocence radiating from her guileless countenance was as ubiquitous as the sunlight at high noon."
    )

    for i, each_inspiration in enumerate(inspirations):
        if i >= 0 and i >= max_number:
            break

        print(f"Generating image {i}: {each_inspiration}...")
        gender = pick(gender_distribution)
        years = pick(age_distribution)

        style = (
            "(close up), dynamic angle portrait, single person, background removed, Andy Warhol/Lichtenstein inspired "
            "style, pop art color palette, comic book aesthetics, "
        )

        meta_prompt = (
            f"Describe a person in a way such that two different people could draw a portrait of this person "
            f"according to your description and it would be obvious that they drew the same person. Describe them "
            f"with comma separated features as follows:\n"
            f"[hair color] [hair style], [eye color] eyes, [ethnicity], [some peculiar feature in their appearance "
            f"that makes them stand out in a crowd]"
            f"\n"
            f"Make sure to replace each bracketed variable with some aspect of the person's appearance. Do not use "
            f"pronouns. Let the description be inspired by your visual idea of \"{each_inspiration}\" but do not "
            f"mention \"{each_inspiration}\" in your description."
        )

        description_file_path = f"faces/person_{i:04d}.txt"
        if os.path.isfile(description_file_path):
            continue

        description = simple_interface.reply_to_prompt(meta_prompt)
        description = description.strip().removesuffix(".").removesuffix(",").strip()
        description = style + description + f", {gender}, {years} years old"
        with open(description_file_path, mode="w") as f:
            f.write(description)


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
    save_images(300)


if __name__ == "__main__":
    main()
