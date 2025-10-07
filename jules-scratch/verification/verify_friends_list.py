import re
from playwright.sync_api import sync_playwright, expect, Page

def create_user(page: Page, name: str, invitation_link: str = None):
    """Helper function to create a new user."""
    if invitation_link:
        page.goto(invitation_link)
    else:
        page.goto("http://localhost:8000")

    # Click "Spiel starten" to begin the user creation process
    start_button = page.get_by_role("button", name="Spiel starten")
    expect(start_button).to_be_visible()
    start_button.click()

    # Enter the user's name in the dialog and press Enter
    name_dialog = page.locator(".q-dialog:has-text('Hallo! Du scheinst neu zu sein.')")
    expect(name_dialog).to_be_visible(timeout=10000)
    name_input = name_dialog.get_by_role("textbox")
    name_input.fill(name)
    name_input.press("Enter")

    # Acknowledge the info dialog
    info_dialog = page.locator(f".q-dialog:has-text('Hallo {name}!')")
    expect(info_dialog).to_be_visible(timeout=10000)
    info_dialog.get_by_role("button", name="OK").click()

    # Wait for the game to load, which indicates user creation is complete
    expect(page).to_have_url(re.compile(r".*/game"), timeout=15000)

    # Store the name_hash from local storage to allow logging back in
    name_hash = page.evaluate("() => localStorage.getItem('name_hash')")
    return name_hash

def login_user(page: Page, name_hash: str):
    """Helper function to log in a user by setting local storage."""
    page.goto("http://localhost:8000")
    page.evaluate(f"localStorage.setItem('name_hash', '{name_hash}')")
    page.reload()

def test_friends_list_and_wins_display():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 1. Create User "Alice"
            print("Creating user Alice...")
            alice_hash = create_user(page, "Alice")
            print(f"Alice created with hash: {alice_hash}")

            # 2. Go back to the start page and get an invitation link
            page.goto("http://localhost:8000")
            expect(page.get_by_role("heading", name="Willkommen zurück, Alice!")).to_be_visible()

            page.get_by_role("button", name="FreundIn einladen").click()
            invite_dialog = page.locator(".q-dialog")
            expect(invite_dialog).to_be_visible()

            link_element = invite_dialog.locator('label:has-text("http://")')
            invitation_link = link_element.inner_text()
            print(f"Got invitation link: {invitation_link}")

            # Close the dialog by pressing Escape
            page.keyboard.press("Escape")

            # 3. Create User "Bob" using the invitation link in a new page
            print("Creating user Bob...")
            bob_page = context.new_page()
            create_user(bob_page, "Bob", invitation_link)
            print("Bob created.")
            bob_page.close()

            # 4. Log back in as Alice to accept the friendship
            print("Logging back in as Alice...")
            login_user(page, alice_hash)
            page.reload() # Reload to ensure friend request dialog appears

            # Accept the friend request
            friend_dialog = page.locator(".q-dialog")
            expect(friend_dialog).to_be_visible(timeout=10000)
            expect(friend_dialog).to_contain_text("Willst du mit Bob befreundet sein?")
            friend_dialog.get_by_role("button", name="ja").click()
            print("Friendship accepted.")

            # 5. Verify the friends list
            print("Verifying friends list...")
            page.reload() # Reload to ensure the friends list is updated
            friends_container = page.locator("div:has(> h2:text('Friends'))")
            expect(friends_container).to_be_visible()

            bob_card = friends_container.locator("div.w-20.md\\:w-40.rounded:has(label:text('Bob'))")
            expect(bob_card).to_be_visible()

            # Verify the "Wins" count is displayed correctly
            wins_label = bob_card.locator("label:has-text('Wins:')")
            expect(wins_label).to_have_text("Wins: 0")
            print("Wins label is correct.")

            # 6. Take the final screenshot
            screenshot_path = "jules-scratch/verification/verification.png"
            page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")

        finally:
            browser.close()

if __name__ == "__main__":
    test_friends_list_and_wins_display()