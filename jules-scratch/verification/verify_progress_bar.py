from playwright.sync_api import sync_playwright, expect
import time

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # 1. Navigate to the application
            page.goto("http://127.0.0.1:5000")

            # 2. Fill in the form
            page.get_by_label("Assunto").fill("Progress Bar Test")

            # Add a few emails to the manual list
            email_input = page.get_by_label("Adicionar destinatário")
            email_input.fill("test1@example.com")
            page.keyboard.press("Enter")
            email_input.fill("test2@example.com")
            page.keyboard.press("Enter")
            email_input.fill("test3@example.com")
            page.keyboard.press("Enter")

            # Fill the message using the correct method
            editor_frame = page.frame_locator('#message_ifr')
            editor_body = editor_frame.locator('body#tinymce')
            expect(editor_body).to_be_visible(timeout=10000)
            page.evaluate("tinymce.get('message').setContent('This is a test message.')")

            # 3. Click the send button
            page.get_by_role("button", name="ENVIAR SINAL").click()

            # 4. Wait for the first progress update
            expect(page.locator("#log-area")).to_contain_text("Email enviado para test1@example.com", timeout=10000)

            # 5. Check the progress bar style
            progress_bar = page.locator("#progress-bar")
            width_str = progress_bar.get_attribute("style")

            percent_str = width_str.split(":")[1].strip().replace("%;", "")
            percent = float(percent_str)

            print(f"Progress bar width is: {percent}%")
            assert 0 < percent < 100, "Progress bar should be in an intermediate state."

            # 6. Take a screenshot
            page.screenshot(path="jules-scratch/verification/progress_bar_works.png")

            print("Verification successful. Screenshot saved.")

        except Exception as e:
            print(f"An error occurred during verification: {e}")

        finally:
            browser.close()

if __name__ == "__main__":
    run_verification()
