import random
from rdkit.Chem import Descriptors
import numpy as np
import hashlib
import os
import sys
sys.path.append(os.path.join(os.environ["CONDA_PREFIX"], "share", "RDKit", "Contrib"))
from SA_Score import sascorer
from rdkit import Chem



class State:
    """State class"""

    def __init__(
        self,
        # size=8,
        goal=2.3406,
        sa_target=0,
        allchoices=["C", "O", "=", "N", "c", "1", "S", "P", "F", "2", "\n"],
        max_value1=20,
        max_value2=5,
        moves=None,
        turn=8,
    ):
        """Class: state of the Node class. Contains information about the

        Args:
                size (int, optional): maximum size of the molecule aka number of atoms in molecule. Defaults to 8.
                goal (float, optional): target value for logP; MCTS must build a molecule that is as close to this target as possible. Defaults to 2.3406.
                sa_target (int, optional): target value for RDKit synthesizability score (SA score); MCTS must build a molecule that is as close to this target as possible. Defaults to 0.
                choices (list, optional): list of SMILES symbols that are options to choose for the next move. Defaults to ['C', 'O', '=', 'N', 'c', '1', 'S', 'P', 'F', '2'].
                max_value1 (int, optional): max value of logP; for normalization of reward calculation. Defaults to 20.
                max_value2 (int, optional): max value of SA score; for normalization of reward calculation. Defaults to 5.
                moves (_type_, optional): list of SMILES symbols that have been selected. Defaults to None.
                turn (int, optional): counter that tracks the turn number, should be equal to size aka every turn corresponds to choosing the next SMILES symbol. Defaults to 8.
        """
        self.turn = turn
        self.moves = moves if moves is not None else []
        self.smiles = "".join(self.moves)
        self.goal = goal
        self.sa_target = sa_target
        self.choices = allchoices.copy()
        self.allchoices = allchoices
        self.max_value1 = max_value1
        self.max_value2 = max_value2
        self.sa_score = None
        self.mae_sa_score = None
        self.logp = None
        self.mae_logp = None

        if len(self.moves) > 0 and self.moves[-1] == '\n':
            self.choices = []

        self.num_moves = len(self.choices)
    def next_state(self):
        """Function to get the next state: For the next move, randomly select a SMILES symbole among the available choices.
        Then, create a new state where this move is added to self.moves and update the turn counter (reduce by one).

        Returns:
                State class: state of the next turn
        """
        try:
            nextmove = random.choice(self.choices)
        except:
            print("FAILED", self.choices)
        next_turn = State(
            moves=self.moves + [nextmove],
            turn=self.turn - 1,
            # size=self.size,
            goal=self.goal,
            sa_target=self.sa_target,
            allchoices=self.allchoices,
            max_value1=self.max_value1,
            max_value2=self.max_value2,
        )
        self.choices.remove(nextmove)
        self.num_moves -= 1
        return next_turn

    def terminal(self):
        """Function to check if the State is terminal. If the turn counter has counted down 0, then the state has reached termination.

        Returns:
                bool: True for terminal, False for non-terminal
        """
        if len(self.moves) > 0 and self.moves[-1] == "\n":
            return True
        if (self.turn == 0):
            return True
        
        return False

    def reward(self):
        """Function to check for SMILES string validity and calculate the corresponding reward.
        If the molecule is valid, then logP and SA score are calculated. A reward for each is calculated by getting the distance from the corresponding target value.
        The final reward is taken as an average of the rewards. One reward can be weighted more than the other.

        Returns:
                float: calculated reward value
        """
        new_compound = "".join(self.moves)
        mol = Chem.MolFromSmiles(new_compound)
        if mol is None:
            reward = 0
            logp = np.nan
            sa_score = np.nan
        else:
            self.logp = Descriptors.MolLogP(mol)
            self.sa_score = sascorer.calculateScore(mol)
            self.mae_sa_score = abs(self.sa_score - self.sa_target)
            self.mae_logp = abs(self.logp - self.goal)
            reward1 = np.max(
                (1.0 - (self.mae_logp / self.max_value1)) * 3, 0
            )  # force no negative reward values
            reward2 = np.max(
                1.0 - (self.mae_sa_score / self.max_value2), 0
            )  # force no negative reward values
            reward = np.mean([reward1, reward2])
        return reward  # , logp, sa_score

    def __hash__(self):
        return int(hashlib.md5(str(self.moves).encode("utf-8")).hexdigest(), 16)

    def __eq__(self, other):
        if hash(self) == hash(other):
            return True
        return False

    def __repr__(self):
        if self.moves:
            if self.logp is None:
                _ = self.reward()
            if self.logp is None:
                logp = mae_logp = np.nan
            else:
                logp, mae_logp = self.logp, self.mae_logp

            if self.logp is None:
                sa_score = mae_sa_score = np.nan
            else:
                sa_score, mae_sa_score = self.sa_score, self.mae_sa_score

            s = (
                f"logP: {logp:.4f}; SA score: {sa_score:.4f};" +
                f"logP MAE: {mae_logp:.4f}; SA MAE: {mae_sa_score:.4f}; state: "
                + self.smiles.replace("\n", ".")
                + "; "
                + f"Moves: {self.moves}"
            )
        else:
            s = "empty state"
        return s

    def __str__(self):
        # s=f"Value: {self.value}; Moves: {self.moves}"
        s = f"Moves: {self.moves}"
        # logger.info(s)
        return s