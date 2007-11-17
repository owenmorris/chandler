#   Copyright (c) 2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


# QuickEntry takes one or more commands, plus additional text, and processes it.
#
# Broadly speaking, processing can mean two different things: A single command
# taking text input and doing something with it, or several commands applied in
# succession to a single "state" object.

class QuickEntryState(object):
    """
    State for one or more QuickEntryCommands to process.

    When all commands have processed a ProcessingState, its finalize method
    should be called.

    """
    def __init__(self, view, text):
        self.view = view
        self.text = text
        self.item = None

    def finalize(self):
        pass

class QuickEntryCommand(object):
    """
    Behavior and meta-data for commands processed as chandler.quick_entry
    entry_points.

    @ivar command_names: A list of synonyms for a command
    @type command_names: A list of strings

    @ivar single_command: True if later commands should be treated as part of 
                          the text passed to process, instead of additional
			  commands
    @type single_command: Boolean

    @ivar state_class: The type of state that should be passed to process
    @type state_class: QuickEntryState

    """
    command_names = []
    single_command = True
    state_class = QuickEntryState

    @classmethod
    def process(cls, state):
        """Process a QuickEntryState."""
        pass

def run_commands(view, text, commands):
    """
    Create a QuickEntryState, run each command on it, finalize the state,
    return state.

    Only commands matching the first command's state_class attributes will be
    applied.

    """
    state = None

    for command in commands:
        if state is None:
            shared_state_class = command.state_class
            state = shared_state_class(view, text)
        if command.state_class == shared_state_class:
            command.process(state)
    if state is not None:
        state.finalize()
        return state
