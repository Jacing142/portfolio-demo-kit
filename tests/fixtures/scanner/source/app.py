"""Invented fixture project for scanner tests. Nothing here is real."""
API_KEY = "sk-ant-api03-FIXTUREonlyNOTREAL0000000000000000000000"
SHEET = "https://docs.google.com/spreadsheets/d/1FixtureSheetIdNotReal0000000000000000000/edit"


def build_prompt(row):
    intro = "You are a careful assistant for the Quillmoor lending desk."
    return intro + " Summarise the applicant note in two sentences for the review panel."
