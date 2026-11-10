# UI verify

Used by: `ui-verifier`, and any node that changes a route, component or user-visible flow. Pause point: before the change is opened. Read-do, in order.

## Killer items
1. Drive the changed flow with headless Playwright, never a visible window that takes focus unless the owner asks to watch. Capture with `shot <url> --env <name> --viewport 1440x900` or the headless tools. Reading the code is not verification.
2. Screenshot each state at a fixed viewport. Put the screenshots in the change as a table.
3. `list_console_messages` is clean: no errors, no unexpected warnings. List any that remain.
4. Test a window and zoom matrix, not one viewport. Look at the shots; do not claim "fits" from exact Playwright sizes (see Reference).
5. A linked design frame is captured at its full frame size and shipped beside the screenshot, differences listed, no verdict. Match to the pixel; only shared platform components override, and they are listed.
6. A state or flow the frame does not show is a question for the designer. Never invent it.

## Reference
Window matrix
- Suggested sizes, to be tuned per app: 1280, 1440 and 1920 wide at 100% zoom, 1440 at 125% and 150%, and one narrow window near 1024.
- Window size and zoom change the usable area. Set the viewport per row, and read the shot for clipping, overflow and hidden controls.

Accessibility floor (W3C Easy Checks)
- Page title, heading order, image alt text, contrast, keyboard operation with visible focus, form labels, text resize to 200%.

States
- Loading, empty and error states exist and match the frame.

Design frame capture
- Frame beats ticket wording when they disagree. Say which one you built.
