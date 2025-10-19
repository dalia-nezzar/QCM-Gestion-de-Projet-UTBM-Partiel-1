import streamlit as st
import json
from difflib import SequenceMatcher

st.set_page_config(page_title="QCM Gestion de Projet - Partiel 1", layout="wide")

def calculate_similarity(user_answer, correct_answer):
    """Calcule le pourcentage de similarité entre deux réponses"""
    # Normaliser les réponses
    user_words = set(user_answer.lower().strip().split())
    correct_words = set(correct_answer.lower().strip().split())
    
    # Calculer l'intersection et l'union
    if len(correct_words) == 0:
        return 1.0 if len(user_words) == 0 else 0.0
    
    intersection = len(user_words & correct_words)
    similarity = intersection / len(correct_words)
    
    return similarity

st.title("Questionnaire à choix multiples")

# Initialiser l'état de session
if "current_question" not in st.session_state:
    st.session_state.current_question = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# Charger les questions depuis le JSON
with open("questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

# Afficher la question actuelle
if not st.session_state.submitted:
    current_q = questions[st.session_state.current_question]
    
    st.subheader(f"Question {st.session_state.current_question + 1}/{len(questions)}")
    st.write(current_q["question"])
    
    # Vérifier le type de question
    if current_q["type"] == "multiple_choice":
        # Vérifier si plusieurs réponses correctes
        if len(current_q["correct"]) > 1:
            # Checkboxes pour réponses multiples
            st.write("*Plusieurs réponses possibles*")
            selected_answers = []
            for option in current_q["options"]:
                if st.checkbox(option, key=f"question_{current_q['id']}_{option}"):
                    selected_answers.append(option)
            st.session_state.answers[current_q["id"]] = selected_answers
        else:
            # Radio buttons pour une seule réponse
            selected_answer = st.radio(
                "Choisir une réponse:",
                current_q["options"],
                key=f"question_{current_q['id']}"
            )
            st.session_state.answers[current_q["id"]] = [selected_answer]
    
    elif current_q["type"] == "free_answer":
        # Déterminer le nombre de réponses attendues
        num_answers = current_q.get("number_of_answers", 1)
        
        if num_answers > 1:
            st.write(f"*Fournissez {num_answers} réponses*")
        
        answers_list = []
        for i in range(num_answers):
            answer = st.text_input(
                f"Réponse {i + 1}:" if num_answers > 1 else "Votre réponse:",
                key=f"question_{current_q['id']}_answer_{i}"
            )
            answers_list.append(answer)
        
        st.session_state.answers[current_q["id"]] = answers_list
    
    # Boutons de navigation
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.current_question > 0:
            if st.button("⬅️ Précédent"):
                st.session_state.current_question -= 1
                st.rerun()
    
    with col3:
        if st.session_state.current_question < len(questions) - 1:
            if st.button("Suivant ➡️"):
                st.session_state.current_question += 1
                st.rerun()
        else:
            if st.button("✅ Soumettre"):
                st.session_state.submitted = True
                st.rerun()

else:
    # Afficher les résultats
    st.success("QCM complété !")
    
    score = 0
    for q in questions:
        if q["id"] in st.session_state.answers:
            if st.session_state.answers[q["id"]] == q["correct"]:
                score += 1
    
    st.metric("Score", f"{score}/{len(questions)}")
    
    # Détail des réponses
    st.subheader("Détail des réponses")
    for q in questions:
        with st.expander(f"Question {q['id']}: {q['question'][:50]}..."):
            user_answer = st.session_state.answers.get(q["id"], [])
            
            # Pour les réponses libres, comparaison insensible à la casse
            if q["type"] == "free_answer":
                user_answers_normalized = [ans.lower().strip() for ans in user_answer if ans.strip()]
                correct_normalized = [c.lower().strip() for c in q["correct"]]
                
                # Vérifier si chaque réponse utilisateur correspond à une réponse correcte
                is_correct = False
                if len(user_answers_normalized) > 0:
                    is_correct = any(
                        ans in correct_normalized or calculate_similarity(ans, correct) >= 0.8
                        for ans in user_answers_normalized
                        for correct in correct_normalized
                    )
            else:
                # Pour les choix multiples, vérifier que toutes les réponses correspondent
                is_correct = set(user_answer) == set(q["correct"])
            
            st.write(f"**Votre réponse:** {', '.join(user_answer) if user_answer else 'Non répondu'}")
            st.write(f"**Bonne(s) réponse(s):** {', '.join(q['correct'])}")
            
            if is_correct:
                st.success("✅ Correct !")
            else:
                st.error("❌ Incorrect !")
    
    # Bouton pour recommencer
    if st.button("🔄 Recommencer"):
        st.session_state.current_question = 0
        st.session_state.answers = {}
        st.session_state.submitted = False
        st.rerun()