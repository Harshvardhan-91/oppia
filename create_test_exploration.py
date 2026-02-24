#!/usr/bin/env python3
"""Script to create a test exploration with feedback for testing the bug."""

import sys
import os

# Add the oppia directory to the path
sys.path.insert(0, os.path.join(os.getcwd()))

from core import feconf
from core.domain import exp_domain
from core.domain import exp_services
from core.domain import rights_manager
from core.domain import state_domain
from core.domain import translation_domain
from core.domain import user_services
from core.platform import models
from core.tests import test_utils

import contextlib

# Initialize the datastore
(user_models,) = models.Registry.import_models([models.Names.USER])


def create_test_exploration():
    """Creates a simple exploration for testing feedback."""

    # You need to replace this with your actual user ID
    # You can get it from: http://localhost:8181/preferences (look in browser dev tools)
    ADMIN_EMAIL = 'testadmin@example.com'  # Change this to your admin email

    # Get user ID
    user_settings = user_services.get_user_settings_from_email(ADMIN_EMAIL)
    if not user_settings:
        print(f"User not found: {ADMIN_EMAIL}")
        print("Please ensure you're logged in and use the correct email.")
        return None

    owner_id = user_settings.user_id

    # Create exploration
    exploration_id = exp_services.get_new_exploration_id()
    print(f"Creating exploration with ID: {exploration_id}")

    exploration = exp_domain.Exploration.create_default_exploration(
        exploration_id,
        title='Test Feedback Bug',
        category='Mathematics',
        objective='Test exploration for feedback bug reproduction',
    )

    # Set up content ID generator
    content_id_generator = translation_domain.ContentIdGenerator(
        exploration.next_content_id_index
    )

    # Configure Introduction state
    init_state = exploration.states[exploration.init_state_name]
    init_state.content.html = 'Welcome to the test! Click continue.'

    # Add Continue Button interaction
    init_state.interaction.id = 'Continue'
    init_state.interaction.customization_args = {}

    # Set default outcome to go to Question state
    question_content_id = content_id_generator.generate(
        translation_domain.ContentType.DEFAULT_OUTCOME
    )
    init_state.interaction.default_outcome = state_domain.Outcome(
        'Question',
        None,
        state_domain.SubtitledHtml(question_content_id, '<p>Continuing...</p>'),
        False,
        [],
        None,
        None,
    )

    # Add Question state
    question_state_content_id = content_id_generator.generate(
        translation_domain.ContentType.CONTENT
    )
    question_state_outcome_id = content_id_generator.generate(
        translation_domain.ContentType.DEFAULT_OUTCOME
    )

    exploration.add_state(
        'Question', question_state_content_id, question_state_outcome_id
    )

    question_state = exploration.states['Question']
    question_state.content.html = 'What is 2 + 2?'

    # Add Number Input interaction
    question_state.interaction.id = 'NumericInput'
    question_state.interaction.customization_args = {}

    # Add answer group for correct answer (4)
    end_content_id = content_id_generator.generate(
        translation_domain.ContentType.FEEDBACK
    )
    answer_group = state_domain.AnswerGroup(
        state_domain.Outcome(
            'End',
            None,
            state_domain.SubtitledHtml(end_content_id, '<p>Correct!</p>'),
            False,
            [],
            None,
            None,
        ),
        [state_domain.RuleSpec('Equals', {'x': 4})],
        [],
        None,
    )
    question_state.interaction.answer_groups = [answer_group]

    # Set default outcome (wrong answer) to stay on Question
    default_feedback_id = content_id_generator.generate(
        translation_domain.ContentType.DEFAULT_OUTCOME
    )
    question_state.interaction.default_outcome = state_domain.Outcome(
        'Question',
        None,
        state_domain.SubtitledHtml(default_feedback_id, '<p>Try again!</p>'),
        False,
        [],
        None,
        None,
    )

    # Add End state
    end_state_content_id = content_id_generator.generate(
        translation_domain.ContentType.CONTENT
    )
    end_state_outcome_id = content_id_generator.generate(
        translation_domain.ContentType.DEFAULT_OUTCOME
    )

    exploration.add_state('End', end_state_content_id, end_state_outcome_id)

    end_state = exploration.states['End']
    end_state.content.html = 'Thanks for testing!'
    end_state.interaction.id = 'EndExploration'
    end_state.interaction.customization_args = {
        'recommendedExplorationIds': {'value': []}
    }
    end_state.interaction.default_outcome = None

    # Update content ID index
    exploration.next_content_id_index = (
        content_id_generator.next_content_id_index
    )

    # Save exploration
    exp_services.save_new_exploration(owner_id, exploration)
    print(f"✅ Exploration created successfully!")

    # Publish exploration
    user_actions_info = user_services.get_user_actions_info(owner_id)
    rights_manager.publish_exploration(user_actions_info, exploration_id)
    print(f"✅ Exploration published!")

    print(
        f"\n🎯 Exploration URL: http://localhost:8181/explore/{exploration_id}"
    )
    print(f"📝 Exploration ID: {exploration_id}")

    return exploration_id


if __name__ == '__main__':
    print("=" * 60)
    print("Creating Test Exploration for Feedback Bug")
    print("=" * 60)
    create_test_exploration()
