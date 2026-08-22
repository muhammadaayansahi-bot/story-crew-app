# Story Crew

A CrewAI crew, wrapped in a Streamlit app, that turns a one-line story idea
into a finished short story.

Not the Travel Crew or the Study Crew from class — this is a fiction-writing
pipeline instead.

## What it does

You type a one-line story idea. Three agents pass the work down the line —
plot outline → full draft → tightened final story — and a fourth, optional
agent gives it a quick reader review. You control the genre and the target
word count from the sidebar, and both actually change the output.

## The agents

| Agent | Role | Job |
|---|---|---|
| **Plotter** | Story Plotter | Turns the idea into a bulleted outline: setup, twist, ending. |
| **Writer** | Fiction Writer | Drafts the full story in prose from the Plotter's outline. |
| **Editor** | Line Editor | Cuts and tightens the draft to hit the target word count without losing the twist. |
| **Critic** *(bonus)* | Reader Critic | Reads the finished story and gives a short honest reaction + a star rating. |

Tasks are chained with `context=[...]` and run through `Process.sequential`,
so each agent only sees the previous agent's output, not the raw idea.

## Sidebar controls

- **Genre** (selectbox) — Fantasy, Sci-Fi, Mystery, Comedy, Horror. Changes
  the tone the Plotter and Writer aim for.
- **Target length** (slider, 100–500 words) — changes how much the Editor
  cuts.
- **Reader review** (checkbox) — turns the bonus Critic agent on or off.

## Bonus features added

- A fourth agent (Reader Critic) that reviews the finished story and rates
  it out of 5.
- A "download story as .txt" button.
- Caching (`st.cache_data`) so re-running the exact same idea/genre/length
  is instant and doesn't spend another API call.
- A checkbox that turns a second output mode (the review) on or off.

## Try it — example input

Type this into the input box, leave the sidebar on Fantasy / 250 words:

> a lighthouse keeper who finds a message in a bottle addressed to them

## Running it yourself

1. Clone this repo.
2. `pip install -r requirements.txt`
3. Add your key locally in `.streamlit/secrets.toml`:
   ```toml
   OPENAI_API_KEY = "sk-..."
   ```
4. `streamlit run app.py`

On Streamlit Community Cloud, set `OPENAI_API_KEY` under
**Settings → Secrets** instead of committing it anywhere. The key is never
written into `app.py` or the repo.

## Safety / cost controls

- API key lives only in Streamlit Secrets / a local, gitignored
  `secrets.toml` — never in code.
- A session run limit (5 runs) stops the app from being hammered.
- `requirements.txt` versions are pinned.
