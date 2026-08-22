import os
import streamlit as st
from crewai import Agent, Task, Crew, Process, LLM

st.set_page_config(page_title="Story Crew", page_icon="📖", layout="wide")

# ---- the key comes from Streamlit secrets, never from the code ----
try:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except (KeyError, FileNotFoundError):
    st.error("No API key found. Add GROQ_API_KEY in Settings -> Secrets.")
    st.stop()

llm = LLM(model="groq/llama-3.3-70b-versatile", temperature=0.4)

MAX_RUNS = 5

GENRES = ["Fantasy", "Sci-Fi", "Mystery", "Comedy", "Horror"]


def build_crew(idea, genre, length_words, want_critic):
    plotter = Agent(
        role="Story Plotter",
        goal=(
            f"Turn a one-line idea into a tight {genre} plot outline "
            f"sized for a {length_words}-word story."
        ),
        backstory=(
            "You've outlined hundreds of short stories for an indie fiction magazine. "
            "You never hand over a scene without knowing exactly how it ends."
        ),
        llm=llm, verbose=False, allow_delegation=False, max_iter=3,
    )

    writer = Agent(
        role="Fiction Writer",
        goal=(
            f"Write a complete {genre} short story of about {length_words} words, "
            "following the plot outline exactly."
        ),
        backstory=(
            "You used to ghostwrite pulp fiction and you write fast and vividly. "
            "You always follow the plot you're given, even if you'd rather improvise."
        ),
        llm=llm, verbose=False, allow_delegation=False, max_iter=3,
    )

    editor = Agent(
        role="Line Editor",
        goal=(
            f"Cut and tighten the draft to land close to {length_words} words "
            "without losing the plot, the twist, or the voice."
        ),
        backstory=(
            "You edited for a magazine with a strict word count that never moved. "
            "Every unnecessary word is an insult to the reader's time."
        ),
        llm=llm, verbose=False, allow_delegation=False, max_iter=3,
    )

    plot_task = Task(
        description=(
            f"The reader's story idea: '{idea}'. Genre: {genre}. "
            f"Target length: {length_words} words. Write a short plot outline: "
            f"setup, rising action, twist, ending."
        ),
        expected_output="A bulleted plot outline with setup, twist, and ending.",
        agent=plotter,
    )

    write_task = Task(
        description=(
            f"Using the outline, write the full {genre} short story. Aim for about "
            f"{length_words} words. Include at least one line of dialogue."
        ),
        expected_output=f"A complete short story of roughly {length_words} words.",
        agent=writer,
        context=[plot_task],
    )

    edit_task = Task(
        description=(
            f"Edit the draft so it lands close to {length_words} words. Cut filler, "
            "tighten sentences, keep the twist and the voice intact. Return only the "
            "final story text - no notes."
        ),
        expected_output="The final, polished short story text only.",
        agent=editor,
        context=[write_task],
    )

    agents = {"plotter": plotter, "writer": writer, "editor": editor}
    tasks = {"plot": plot_task, "write": write_task, "edit": edit_task}

    if want_critic:
        critic = Agent(
            role="Reader Critic",
            goal="Give a short, honest reader's-eye reaction to the finished story.",
            backstory=(
                "You represent an ordinary reader, not a literature professor. "
                "No flattery, no essay - just a straight reaction."
            ),
            llm=llm, verbose=False, allow_delegation=False, max_iter=3,
        )
        critic_task = Task(
            description=(
                "Read the final story as an ordinary reader would. Give a 2-3 "
                "sentence reaction and a rating out of 5 stars."
            ),
            expected_output="A short reader reaction ending in an X/5 star rating.",
            agent=critic,
            context=[edit_task],
        )
        agents["critic"] = critic
        tasks["critic"] = critic_task

    return agents, tasks


def run_one(agent, task):
    return str(Crew(agents=[agent], tasks=[task],
                    process=Process.sequential, verbose=False).kickoff())


for k, v in [("runs", 0), ("story", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ---- sidebar ----
with st.sidebar:
    st.markdown("### 👥 Your crew")
    st.markdown("**🗺️ Plotter** — builds the outline\n\n"
                "**✍️ Writer** — drafts the story\n\n"
                "**✂️ Editor** — tightens it to length\n\n"
                "**⭐ Critic** — reviews it (optional)")
    st.divider()
    genre = st.selectbox("🎭 Genre", GENRES)
    length_words = st.slider("📏 Target length (words)", 100, 500, 250, step=50)
    want_critic = st.checkbox("⭐ Get a reader review", value=True)
    st.divider()
    st.markdown(f"**Runs left:** {MAX_RUNS - st.session_state.runs}")
    if st.session_state.story and st.button("🔄 Start over", use_container_width=True):
        st.session_state.story = None
        st.rerun()

# ---- main ----
st.title("📖 Story Crew")
st.caption("Four AI agents turn a one-line idea into a finished short story.")

idea = st.text_input(
    "What's your story idea?",
    placeholder="e.g. a lighthouse keeper who finds a message in a bottle addressed to them",
    max_chars=200,
)

if st.button("🚀 Build my story", type="primary", use_container_width=True):
    if st.session_state.runs >= MAX_RUNS:
        st.error("You have used all your runs. Refresh the page to reset.")
    elif len(idea.strip()) < 5:
        st.warning("Type a story idea first.")
    else:
        i = idea.strip()
        try:
            agents, tasks = build_crew(i, genre, length_words, want_critic)

            with st.status("🗺️ Plotter is building the outline...") as s:
                outline = run_one(agents["plotter"], tasks["plot"])
                s.update(label="🗺️ Outline is ready", state="complete")

            # hand the outline to the writer by hand
            tasks["write"].description += f"\n\nTHE OUTLINE:\n{outline}"

            with st.status("✍️ Writer is drafting the story...") as s:
                draft = run_one(agents["writer"], tasks["write"])
                s.update(label="✍️ First draft is ready", state="complete")

            # hand the draft to the editor by hand
            tasks["edit"].description += f"\n\nTHE DRAFT:\n{draft}"

            with st.status("✂️ Editor is tightening the draft...") as s:
                final_story = run_one(agents["editor"], tasks["edit"])
                s.update(label="✂️ Final story is ready", state="complete")

            review = None
            if want_critic:
                tasks["critic"].description += f"\n\nTHE STORY:\n{final_story}"
                with st.status("⭐ Critic is reading it...") as s:
                    review = run_one(agents["critic"], tasks["critic"])
                    s.update(label="⭐ Review is ready", state="complete")

            st.session_state.runs += 1
            st.session_state.story = {
                "idea": i, "genre": genre, "length_words": length_words,
                "outline": outline, "story": final_story, "review": review,
            }
            st.rerun()

        except Exception as e:
            st.error("Something went wrong.")
            st.caption(f"{type(e).__name__}: {e}")

s = st.session_state.story
if s:
    st.divider()
    st.subheader(f"📖 {s['genre']} · ~{s['length_words']} words")

    tab_labels = ["📖 Final story", "🗺️ Plot outline"]
    if s["review"]:
        tab_labels.append("⭐ Reader review")
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        st.write(s["story"])
    with tabs[1]:
        st.markdown(s["outline"])
    if s["review"]:
        with tabs[2]:
            st.info(s["review"])

    download_text = (
        f"IDEA: {s['idea']}\nGENRE: {s['genre']}\n\n"
        f"=== FINAL STORY ===\n{s['story']}\n\n"
        f"=== PLOT OUTLINE ===\n{s['outline']}"
    )
    if s["review"]:
        download_text += f"\n\n=== READER REVIEW ===\n{s['review']}"

    st.download_button(
        "⬇️ Download the story",
        data=download_text,
        file_name=f"story_{s['genre'].lower()}.txt",
        mime="text/plain",
    )
