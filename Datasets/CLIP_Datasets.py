# -*- coding: utf-8 -*-
"""
Created on Wed Aug  7 16:51:54 2024

@author: Yiyang Liu
"""
import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
plt.style.use('fivethirtyeight')
import warnings
import os, sys
import cv2
from torchvision import transforms
from transformers import AutoImageProcessor, AutoModel
from transformers import BertTokenizer
import torch
from PIL import Image
import requests
from transformers import Dinov2Config, Dinov2Model
from transformers import ViTModel, ViTFeatureExtractor
import io
import spacy

class Meme_DataSet():
    
        
    def __init__(self, img_dir, text_file ='Datasets/TEXT_sentences.csv', label = 'Datasets/Sentiments.csv' ,img_model = 'DINOv2', text_model = 'DistilledBert'):
    
        

        self.text_path = text_file
        self.labelpath = label
        self.img_dir = img_dir
        self.text_tokenizer =None
        self.img_preprocess = None
        if img_model == 'DINOv2':
            self.img_preprocess = AutoImageProcessor.from_pretrained('facebook/dinov2-base')
        
        # Fill in the efficient net
        if text_model == 'DistilledBert':
            self.text_tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        self.images = []
        self.text = []
        self.label = []
        self.nlp = spacy.load("en_core_web_sm")

    def __len__(self):
        item_list = os.listdir(self.img_dir)
        return len(item_list)

    def __getitem__(self, idx):
        
        maxlength = 60
        text = pd.read_csv(self.text_path)
        label = pd.read_csv(self.labelpath)
        self.label = list(label['sarcasm'])[idx]
        self.text = list(text['text_corrected'])[idx]
        
        doc = self.nlp(self.text)
        lemmatized_words = [token.lemma_ for token in doc if not token.is_stop]
        self.text = ' '.join(lemmatized_words)
        ct = len(os.listdir(self.img_dir)[idx])
        img_path = os.path.join(self.img_dir, os.listdir(self.img_dir)[idx])
     
        
        transform = transforms.Compose([
                               transforms.ToPILImage(),
                               transforms.Resize((224, 224)),
                               transforms.ToTensor()
                                ])
        

        
        with open(img_path, 'rb') as file:
            corrupted_data = file.read()
        
        # clean corrupted images. strip the last byte
        img = Image.open(io.BytesIO(corrupted_data))
        
        
        img = img.convert("RGB")
        
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        cleaned_data = buffer.getvalue()
        
        im = Image.open(io.BytesIO(cleaned_data))
        image_batch = transform(im)
        
           
   
        if self.img_preprocess:
            image = self.img_preprocess(images = image_batch, return_tensors = 'pt',do_rescale=False)
 
            
        
        
        #CAPTION at entry 1

        text_batch = self.text_tokenizer.encode_plus(
            self.text,
            add_special_tokens=True,  # Add [CLS] and [SEP]
            max_length=maxlength,
            padding='max_length',
            truncation=True,  # Truncate to max_length
            return_attention_mask=True,  # Return attention masks
            return_tensors='pt'  # Return PyTorch tensors
            
            )
        
        print(text_batch['input_ids'])
      
        
        return {'image': image['pixel_values'], 'input_ids': text_batch['input_ids'], 'attention': text_batch['attention_mask'], 'label': self.label}
    
    def getimages(self, idx):
        '''
        Used to return unprocessed image

        '''
        for i in idx:
            item = os.listdir(self.img_dir)[i]
            img_path = os.path.join(self.img_dir,item)
            image = cv2.imread(img_path)
            #image = cv2.resize(image,(224, 224,3))
            self.images.append(image)
            
        return self.images
    

    
    
    
    
    
    
    
    
#
#-----------------------------
class Meme_Classify():
    
        
    def __init__(self, img_dir, text_file ='Datasets/TEXT_sentences.csv', label = 'Datasets/Sentiments.csv' ,img_model = 'DINOv2', text_model = 'Bert'):
    
        self.nlp = spacy.load("en_core_web_sm")

        self.text_path = text_file
        self.labelpath = label
        self.img_dir = img_dir
        self.text_tokenizer =None
        self.img_preprocess = None
        if img_model == 'DINOv2':
            self.img_preprocess = AutoImageProcessor.from_pretrained('facebook/dinov2-base')
        
        # Fill in the efficient net
        if text_model == 'Bert':
            self.text_tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        self.images = []
        self.text = []
        self.label = []
        self.raw_label = []

    def __len__(self):
        item_list = os.listdir(self.img_dir)
        return len(item_list)

    def __getitem__(self, idx):
        
  
        maxlength = 30 # REMEMBER TO ADJUST THIS!!!!!!!!
        text = pd.read_csv(self.text_path)
        label = pd.read_csv(self.labelpath)
        
        label = label['sarcasm'].tolist()
        l = label[idx]
        if l == 1:
            self.label = 'a sarcastic meme'
            self.raw_label = l
            
 
        else:
            self.label = 'a regular meme'
            self.raw_label = l
        

        #Lemmatization and filter stop words
       
        tt = text['text_corrected'].tolist()
        self.text = tt[idx]
        doc = self.nlp(self.text)
        lemmatized_words = [token.lemma_ for token in doc if not token.is_stop]
        self.text = ' '.join(lemmatized_words)
        
        #self.text = self.text + self.label
    
        ct = len(os.listdir(self.img_dir)[idx])
        img_path = os.path.join(self.img_dir, os.listdir(self.img_dir)[idx])
     
        
        transform = transforms.Compose([
                               transforms.Resize((224, 224)),
                               transforms.ToTensor(),
                               transforms.ColorJitter(brightness=.3, hue=.2),
                               transforms.Normalize((0.48145466, 0.4578275, 0.40821073),(0.26862954, 0.26130258, 0.27577711)),
                                ])
        
    
        
        with open(img_path, 'rb') as file:
            corrupted_data = file.read()
        
        # clean corrupted images. strip the last byte
        img = Image.open(io.BytesIO(corrupted_data))
        
        
        img = img.convert("RGB")
        
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        cleaned_data = buffer.getvalue()
        
        im = Image.open(io.BytesIO(cleaned_data))
        image_batch = transform(im)

           
   
        if self.img_preprocess:
            #image = self.img_preprocess(images = image_batch, return_tensors = 'pt', do_rescale = False)
            pass
 
            
        
        
        #CAPTION at entry 1
      
   
        text_batch = self.text_tokenizer.encode_plus(
            self.text + self.label,
            add_special_tokens=True,  # Add [CLS] and [SEP]
            max_length=maxlength,
            padding='max_length',
            truncation=True,  # Truncate to max_length
            return_attention_mask=True,  # Return attention masks
            return_tensors='pt'  # Return PyTorch tensors
            
            )
          
        #return {'image': image['pixel_values'], 'input_ids': text_batch['input_ids'], 'attention': text_batch['attention_mask'], 'label': self.raw_label}
        return {'image': image_batch, 'input_ids': text_batch['input_ids'], 'attention': text_batch['attention_mask'], 'label': self.raw_label}
    
    def getimages(self, idx):
        '''
        Used to return unprocessed image

        '''
        for i in idx:
            item = os.listdir(self.img_dir)[i]
            img_path = os.path.join(self.img_dir,item)
            image = cv2.imread(img_path)
            #image = cv2.resize(image,(224, 224,3))
            self.images.append(image)
            
        return self.images

    
class Meme_Verify():
    
        
    def __init__(self, img_dir, label = 'Datasets/Sentiments.csv' ,img_model = 'DINOv2', text_model = 'DistilledBert'):
    
        self.nlp = spacy.load("en_core_web_sm")

      
        self.labelpath = label
        self.img_dir = img_dir
        self.text_tokenizer =None
        self.img_preprocess = None
        if img_model == 'DINOv2':
            self.img_preprocess = AutoImageProcessor.from_pretrained('facebook/dinov2-base')
        
        # Fill in the efficient net
        if text_model == 'DistilledBert':
            self.text_tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        self.images = []
 
        self.label = []

    def __len__(self):
        item_list = os.listdir(self.img_dir)
        return len(item_list)

    def __getitem__(self, idx):
        
        maxlength = 128 # REMEMBER TO ADJUST THIS!!!!!!!!
    
        label = pd.read_csv(self.labelpath)
        if list(label['sarcasm'])[idx] == 1:
            self.label = 'a sarcastic meme'
        else:
            self.label = 'a regular meme'
            
        #Lemmatization and filter stop words
       
    
 
    
        ct = len(os.listdir(self.img_dir)[idx])
        img_path = os.path.join(self.img_dir, os.listdir(self.img_dir)[idx])
     
        
        transform = transforms.Compose([
                               
                               transforms.Resize((224, 224)),
                               transforms.ToTensor().permute(2, 0, 1).float()
                                ])
        
       
        
        
        with open(img_path, 'rb') as file:
            corrupted_data = file.read()
        
        # clean corrupted images. strip the last byte
        img = Image.open(io.BytesIO(corrupted_data))
        
        
        img = img.convert("RGB")
        
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        cleaned_data = buffer.getvalue()
        
        im = Image.open(io.BytesIO(cleaned_data))
        image_batch = transform(im)
        
           
   
        if self.img_preprocess:
            image = self.img_preprocess(images = image_batch, return_tensors = 'pt')
 
            
        
        
        #CAPTION at entry 1

        text_batch = self.text_tokenizer.encode_plus(
            self.label,
            add_special_tokens=True,  # Add [CLS] and [SEP]
            max_length=maxlength,
            padding='max_length',
            truncation=True,  # Truncate to max_length
            return_attention_mask=True,  # Return attention masks
            return_tensors='pt'  # Return PyTorch tensors
            
            )
        
        
        return {'image': image['pixel_values'], 'input_ids': text_batch['input_ids'], 'attention': text_batch['attention_mask']}
    
    def getimages(self, idx):
        '''
        Used to return unprocessed image

        '''
        for i in idx:
            item = os.listdir(self.img_dir)[i]
            img_path = os.path.join(self.img_dir,item)
            image = cv2.imread(img_path)
            #image = cv2.resize(image,(224, 224,3))
            self.images.append(image)
            
        return self.images



        
