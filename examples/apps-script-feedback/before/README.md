# Workstyle feedback writer (internal)

EVERYTHING IN THIS FOLDER IS INVENTED for testing portfolio-demo-kit. The company, people,
questionnaire and key are fictional. It contains planted fake personal data and a fake API key on purpose.

Owner: Brackenfold Tiles people team. Ask Wren Castellane before changing the prompt.
Live sheet: https://docs.google.com/spreadsheets/d/1bRkFoLdTiLeSFeEdBaCkEXAMPLE0nlyN0tRealSheet42/edit
Web app: https://script.google.com/a/macros/brackenfold-tiles.test/s/AKfycbEXAMPLEonlyNotARealDeployment99/exec

How it runs: staff fill in the Quadrant-4 Workstyle Check (our own 8-question form). Each night
writeAllFeedback() scores the four traits, compares them with the target grid for the person's
role, and asks the model for a short feedback note. Wren reads every note before it is emailed.
