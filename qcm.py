import streamlit as st
import json
import random
from difflib import SequenceMatcher

st.set_page_config(page_title="QCM - Gestion de Projet Partiel 1", layout="centered")

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
if "show_result" not in st.session_state:
    st.session_state.show_result = False
if "started" not in st.session_state:
    st.session_state.started = False
if "num_questions_selected" not in st.session_state:
    st.session_state.num_questions_selected = None
if "question_file" not in st.session_state:
    # Valeur par défaut (sera remplacée si l'utilisateur choisit autre chose)
    st.session_state.question_file = "questions.json"

# Page d'accueil - choix de la partie puis sélection du nombre de questions
parts = {
    "Partie 1 - GDP": "questions.json",
    "Partie 2 - Coûts, COCOMO": "questions_2.json",
    "Partie 3 - Médian du 09/03/2026": "questions_3.json"
}

if not st.session_state.started:
    st.write("")
    st.write("")
    st.info("👋 Bienvenue dans ce QCM d'entraînement !")
    st.write("Choisissez la partie à utiliser puis le nombre de questions :")

    # Sélecteur de partie (ne modifie session_state.question_file qu'au démarrage)
    selected_part_label = st.selectbox(
        "Choix de la partie:",
        options=list(parts.keys()),
        index=0,
        label_visibility="collapsed"
    )
    selected_file = parts[selected_part_label]

    # Charger les questions de la partie sélectionnée pour déterminer le nombre possible
    with open(selected_file, "r", encoding="utf-8") as f:
        part_questions = json.load(f)

    num_questions = st.selectbox(
        "Sélectionnez le nombre de questions:",
        options=list(range(1, len(part_questions) + 1)),
        index=len(part_questions) - 1,
        label_visibility="collapsed"
    )

    st.write("")
    if st.button("🚀 Commencer", use_container_width=True):
        st.session_state.started = True
        st.session_state.num_questions_selected = num_questions
        st.session_state.question_file = selected_file
        st.session_state.question_order = list(range(len(part_questions)))
        random.shuffle(st.session_state.question_order)
        st.session_state.question_order = st.session_state.question_order[:num_questions]
        st.rerun()
else:
    # Charger les questions depuis le fichier choisi
    with open(st.session_state.question_file, "r", encoding="utf-8") as f:
        all_questions = json.load(f)

    # Récupérer la question actuelle en fonction de l'ordre aléatoire
    current_question_idx = st.session_state.question_order[st.session_state.current_question]
    current_q = all_questions[current_question_idx]

if st.session_state.started and not st.session_state.submitted:
    st.subheader(f"Question {st.session_state.current_question + 1}/{len(st.session_state.question_order)}")
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
    
    # Bouton Valider
    if st.button("✅ Valider cette question"):
        st.session_state.show_result = True
        st.rerun()

# Afficher le résultat si demandé
if st.session_state.show_result and not st.session_state.submitted:
    st.divider()
    st.subheader("Résultat")
    
    user_answer = st.session_state.answers.get(current_q["id"], [])
    
    # Calculer si c'est correct
    if current_q["type"] == "free_answer":
        user_answers_normalized = [ans.lower().strip() for ans in user_answer if ans.strip()]
        correct_normalized = [c.lower().strip() for c in current_q["correct"]]
        
        # Vérifier si chaque réponse utilisateur correspond à une réponse correcte
        is_correct = False
        if len(user_answers_normalized) > 0:
            is_correct = any(
                ans in correct_normalized or calculate_similarity(ans, correct) >= 0.8
                for ans in user_answers_normalized
                for correct in correct_normalized
            )
    else:
        # Pour les choix multiples
        is_correct = set(user_answer) == set(current_q["correct"])
    
    st.write(f"**Votre réponse:** {', '.join(user_answer) if user_answer else 'Non répondu'}")
    st.write(f"**Bonne(s) réponse(s):** {', '.join(current_q['correct'])}")
    
    if is_correct:
        st.success("✅ Correct !")
    else:
        st.error("❌ Incorrect !")
    
    st.divider()
    
    # Boutons de navigation
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.current_question > 0:
            if st.button("⬅️ Précédent"):
                st.session_state.current_question -= 1
                st.session_state.show_result = False
                st.rerun()
    
    with col3:
        if st.session_state.current_question < len(st.session_state.question_order) - 1:
            if st.button("Suivant ➡️"):
                st.session_state.current_question += 1
                st.session_state.show_result = False
                st.rerun()
        else:
            if st.button("🏁 Terminer le QCM"):
                st.session_state.submitted = True
                st.rerun()

# Afficher les résultats finaux
if st.session_state.submitted:
    st.success("QCM complété !")
    
    score = 0
    questions_to_check = [all_questions[idx] for idx in st.session_state.question_order]
    for q in questions_to_check:
        user_answer = st.session_state.answers.get(q["id"], [])
        
        if q["type"] == "free_answer":
            user_answers_normalized = [ans.lower().strip() for ans in user_answer if ans.strip()]
            correct_normalized = [c.lower().strip() for c in q["correct"]]
            
            if len(user_answers_normalized) > 0:
                if any(
                    ans in correct_normalized or calculate_similarity(ans, correct) >= 0.8
                    for ans in user_answers_normalized
                    for correct in correct_normalized
                ):
                    score += 1
        else:
            if set(user_answer) == set(q["correct"]):
                score += 1
    
    st.metric("Score", f"{score}/{len(st.session_state.question_order)}")
    
    # Détail des réponses
    st.subheader("Détail des réponses")
    for i, idx in enumerate(st.session_state.question_order):
        q = all_questions[idx]
        with st.expander(f"Question {i + 1}: {q['question'][:50]}..."):
            user_answer = st.session_state.answers.get(q["id"], [])
            
            if q["type"] == "free_answer":
                user_answers_normalized = [ans.lower().strip() for ans in user_answer if ans.strip()]
                correct_normalized = [c.lower().strip() for c in q["correct"]]
                
                is_correct = False
                if len(user_answers_normalized) > 0:
                    is_correct = any(
                        ans in correct_normalized or calculate_similarity(ans, correct) >= 0.8
                        for ans in user_answers_normalized
                        for correct in correct_normalized
                    )
            else:
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
        st.session_state.show_result = False
        st.session_state.started = False
        st.session_state.num_questions_selected = None
        st.rerun()