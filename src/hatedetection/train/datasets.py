"""
Provides a convenient way to work with text datasets with torch.
"""
from typing import List

import torch
import numpy as np
from transformers import PreTrainedTokenizer
from transformers.data.processors.utils import InputFeatures

class ClassificationDataset(torch.utils.data.Dataset):
    """
    Provides a convenient way to work with text classification datasets in `torch` and
    `transformers`. This class handles the data transformation from text samples to tensors in
    `torch` and transformed outputs are ready to be used in `transformers` pipelines.
    """
    def __init__(self, examples: List[str], labels: List[str],
                 tokenizer: PreTrainedTokenizer, max_length: int = 400):
        #return_tensors='pt' tokenizer.model_max_length
        self.batch_encoding = tokenizer.batch_encode_plus(list(examples),
                                                          padding='longest',
                                                          truncation=True,
                                                          max_length=max_length,
                                                          return_attention_mask=True,
                                                          return_tensors = None)
        self.batch_labels = list(labels)
        self.batch_size = len(examples)

        label_list = np.unique(labels)
        self.label_map = { label: idx for idx, label in enumerate(label_list) }

    def __getitem__(self, idx: int):
        inputs = { feat: self.batch_encoding[feat][idx] for feat in self.batch_encoding }
        return InputFeatures(**inputs, label=self.label_map[self.batch_labels[idx]])

    def __len__(self) -> int:
        return self.batch_size

    def get_labels(self) -> List[str]:
        """
        Gets the list of all the labels in the dataset.
        """
        return list(self.label_map.keys())
