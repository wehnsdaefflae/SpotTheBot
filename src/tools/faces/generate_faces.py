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

        return reply

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
        meta_prompt = (
            f"Describe a person, such that two different people could draw a portrait of this person according to your "
            f"description and it would be obvious that they drew the same person. Come up with the following "
            f"features:\n"
            f"\n"
            f"1. hair style\n"
            f"2. hair color\n"
            f"3. eye color\n"
            f"4. ethnicity\n"
            f"5. some peculiar feature in their appearance that makes them stand out in a crowd\n"
            f"\n"
            f"Respond with a list of short items. Let the description be inspired by your visual idea of "
            f"\"{each_inspiration}\" but do not mention \"{each_inspiration}\" or anything similar in your description."
        )

        draw_prompt = (
            f"Create a single colored, comic-style portrait of the person above. The image should use vibrant colors "
            f"typical of comic art, with clear outlines and minimal shading.\n"
            f"\n"
            f"IMPORTANT:\n"
            f"+ show every single detail mentioned in the description\n"
            f"+ take care to precisely reflect the mentioned age\n"
            f"+ show only the person, show them only once, don't show anything else"
        )

        description_file_path = f"faces/person_{i:04d}.txt"
        if os.path.isfile(description_file_path):
            with open(description_file_path, mode="r") as f:
                description = f.read()
        else:
            description = simple_interface.reply_to_prompt(meta_prompt)
            gender = pick(gender_distribution)
            years = pick(age_distribution)
            description = description.strip() + f"\n\nThe person is {gender} and about {years} old.\n"
            with open(description_file_path, mode="w") as f:
                f.write(description)

        file_name_happy = f"faces/person_{i:04d}_happy.png"
        if not os.path.isfile(file_name_happy):
            print(f"Generating image of happy person {each_inspiration}...")
            happy_description = (
                    "```\n" +
                    description.strip() + "\n\n" + description_happy + "\n" +
                    "```\n\n" +
                    draw_prompt
            )
            simple_interface.save_image(happy_description, file_name_happy)

        file_name_naive = f"faces/person_{i:04d}_naive.png"
        if not os.path.isfile(file_name_naive):
            print(f"Generating image of naive person {each_inspiration}...")
            naive_description = (
                    "```\n" +
                    description.strip() + "\n\n" + description_naive + "\n" +
                    "```\n\n" +
                    draw_prompt
            )
            simple_interface.save_image(naive_description, file_name_naive)

        file_name_anxious = f"faces/person_{i:04d}_anxious.png"
        if not os.path.isfile(file_name_anxious):
            print(f"Generating image of anxious person {each_inspiration}...")
            paranoid_description = (
                    "```\n" +
                    description.strip() + "\n\n" + description_anxious + "\n" +
                    "```\n\n" +
                    draw_prompt
            )
            simple_interface.save_image(paranoid_description, file_name_anxious)

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
    save_images(10)


if __name__ == "__main__":
    main()
