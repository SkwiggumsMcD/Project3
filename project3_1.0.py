import sys
import random
import numpy as np
import pandas as pd
import PIL as pl#pillow's modul
import glob
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras import layers
from tensorflow.keras import optimizers
from tensorflow.keras.utils import to_categorical
import matplotlib.pyplot as plt
import sklearn.metrics
from sklearn.metrics import classification_report, confusion_matrix

class preprocess:
    def _init_(self):
        rpint('init')

    def firsttimerun(self):#only run this once to create the needed datasets. Takes a ton of time to re-build datasets everytime
        ##pulling in test and training data and combining into tensorflow datasets
        val_labels=pd.read_csv("fairface_label_val.csv")
        val_labels=val_labels.to_numpy()#keras can work with datasets or arrays but not both. Converting to array
        train_labels=pd.read_csv("fairface_label_train.csv")
        train_labels=train_labels.to_numpy()#keras can work with datasets or arrays but not both. Converting to array
        train_labels=train_labels[:,0:4]
        val_labels=val_labels[:,0:4]#removing service test category since tensorflow doesn't like bools

        #pulling in image data 
        glob.iglob("C:/Users/vwilso17/Documents/Grad School/COSC525Deeplearning/code/projects/project3/*")
        train_images = [] 
        for f in range(len(train_labels[:,0])):
            train_images.append(np.asarray(pl.Image.open(train_labels[f,0])))
        train_images = np.array(train_images)
        #train_extremes=[min(train_images.reshape(86744*1024)),max(train_images.reshape(86744*1024))]#min-max scaling if datasets were different,, commented out because scanning through each time takes forever
        train_extremes=[0,255]
        train_images=(train_images-train_extremes[1])/(train_extremes[1]-train_extremes[0])

        val_images = [] 
        for f in range(len(val_labels[:,0])):
            val_images.append(np.asarray(pl.Image.open(val_labels[f,0])))
        val_images = np.array(val_images)
        #val_extremes=[min(val_images.reshape(10954*1024)),max(val_images.reshape(10954*1024))]#min-max scaling
        val_extremes=[0,255]
        val_images=(val_images-val_extremes[1])/(val_extremes[1]-val_extremes[0])

        #reshaping image data by flattening 32x32 image data to 1x1024. Converting to float for keras
        train_images=train_images.reshape(86744,1024)
        train_images=train_images.astype('float32')
        val_images=val_images.reshape(10954,1024)
        val_images=val_images.astype('float32')

        #writing pre-processed data to csv
        train_images = pd.DataFrame(train_images)
        train_images.to_csv("trainimages.csv")
        val_images = pd.DataFrame(val_images)
        val_images.to_csv("valimages.csv")
        train_labels = pd.DataFrame(train_labels)
        train_labels.to_csv("trainlabels.csv")
        val_labels = pd.DataFrame(val_labels)
        val_labels.to_csv("vallabels.csv")

        
    def runeverytime(self):#reads in csv files first time pre-processing wrote
        train_images=pd.read_csv("trainimages.csv")
        train_images=train_images.to_numpy()
        train_images=np.delete(train_images,0,1)
        train_labels=pd.read_csv("trainlabels.csv")
        train_labels=train_labels.to_numpy()
        train_labels=np.delete(train_labels,0,1)
        val_images=pd.read_csv("valimages.csv")
        val_images=val_images.to_numpy()
        val_images=np.delete(val_images,0,1)
        val_labels=pd.read_csv("vallabels.csv")
        val_labels=val_labels.to_numpy()
        val_labels=np.delete(val_labels,0,1)

         #giving string entries numerical values will correspond to index in label array
        #age 0=0-2, 1=10-19, 2=20-29, 3=3-9, 4=30-39, 5=40-49, 6=50-59, 7=60-69, 8=more than 70
        #gender 0=male, 1=female
        #race 0=Black, 1=East Asian, 2=Indian, 3=Latino_Hispanic, 4=Middle Eastern, 5= Southeast Asian, 6=White
        agelabels=np.unique(train_labels[:,1])
        genderlabels=np.unique(train_labels[:,2])
        racelabels=np.unique(train_labels[:,3])
        categories=[agelabels,genderlabels,racelabels]#all possible categories to be classified
        
        return train_images,train_labels,val_images,val_labels,categories

class labelvalues:#for replacing string labels with numeric or numeric labels with string
    def _init_(self):
        print('init')
    #encode array should be one of the category label arrays, data array should be one of the
    #label arrays used in training or validation
    def encode(self,dataarray,encodearray):
        self.dataarray=dataarray
        self.encodearray=encodearray
        for i in range(np.size(self.encodearray)):
            indices=(self.dataarray[:]==self.encodearray[i])
            self.dataarray[indices]=i
        return self.dataarray
    def extract(self,dataarray,encodearray):
        self.dataarray=dataarray
        self.encodearray=encodearray
        for i in range(np.size(self.encodearray)):
            indices=(self.dataarray[:]==i)
            self.dataarray[indices]=self.encodearray[i]
        return self.dataarray




## Task 1, FCNN
class networks: 
    def __init__(self,tasknum,xtrain,ytrain,xval,yval,categories):
        print('init')#never prints
        self.tasknum=tasknum
        self.xtrain=xtrain
        self.xtrain=self.xtrain.astype('float32')
        self.ytrain=ytrain
        self.xval=xval
        self.xval=self.xval.astype('float32')
        self.yval=yval
        self.categories=categories
        

        #converting strings to numeric so Keras can use labels
        self.ytrain=self.ytrain[:,self.tasknum+1]
        self.yval=self.yval[:,self.tasknum+1]
        encode=labelvalues()
        #self.ytraintruth=encode.encode(self.ytrain,categories[self.tasknum])
        self.ytrain,b=pd.factorize(self.ytrain)
        self.ytrain=keras.utils.to_categorical(self.ytrain)
        self.ytrain=self.ytrain.astype('int32')
        #self.yvaltruth=encode.encode(self.yval,categories[self.tasknum])
        self.yval,b=pd.factorize(self.yval)
        self.yval=keras.utils.to_categorical(self.yval)
        self.yval=self.yval.astype('int32')
    
    def fcnn(self,lr=0.5,lrfactor=0.2,mom=0.1,epochs=10):#lr=learning rate, lrd=learning rate decay, mom=momentum,tasknum=what to classify
        self.lr=lr
        self.lrfactor=lrfactor
        self.mom=mom
        self.epochs=epochs

        #network set-up 
        model=keras.Sequential()
        model.add(keras.Input(shape=(1024,)))
        model.add(layers.Dense(1024, activation="tanh"))
        model.add(layers.Dense(512, activation="sigmoid"))
        model.add(layers.Dense(100, activation="relu"))
        if self.tasknum==0:#classify based on age
            model.add(layers.Dense(9,activation="softmax"))
        elif self.tasknum==1:#classify based on gender
            model.add(layers.Dense(2,activation="softmax"))
        else:#classify based on race
            model.add(layers.Dense(7,activation="softmax"))
        model.summary()
    
        model.compile(
        optimizer=keras.optimizers.SGD(learning_rate=self.lr,momentum=self.mom),#default lr=0.01, default mom=0.0
        loss=keras.losses.CategoricalCrossentropy(),
        metrics=[keras.metrics.CategoricalAccuracy()],
        )
        
        #training and validating
        print('training and validating')
        reduce_lr = keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=self.lrfactor, patience=1, min_lr=0.0001,mode='min')
        history=model.fit(self.xtrain,self.ytrain,validation_split=0.1,epochs=self.epochs,callbacks=[reduce_lr])#if you don't specify a batch size, it uses 32 for mini-batch GD
        #testing
        print('evalauting')
        results=model.evaluate(self.xval,self.yval)
        print('predicting')
        #predicting
        predictions = model.predict_classes(self.xval)
        
        #plotting/final results summary, from https://machinelearningmastery.com/display-deep-learning-model-training-history-in-keras/
        plt.plot(history.history['categorical_accuracy'])
        plt.plot(history.history['val_categorical_accuracy'])
        if self.tasknum==0:#classify based on age
            plt.title('model accuracy for age classification')
        elif self.tasknum==1:#classify based on gender
            plt.title('model accuracy for gender classification')
        else:#classify based on race
            plt.title('model accuracy for race classification')
        plt.ylabel('accuracy')
        plt.xlabel('epoch')
        plt.legend(['train', 'validation'], loc='upper left')
        plt.show()

        plt.plot(history.history['loss'])
        plt.plot(history.history['val_loss'])
        if self.tasknum==0:#classify based on age
            plt.title('model loss for age classification')
        elif self.tasknum==1:#classify based on gender
            plt.title('model loss for gender classification')
        else:#classify based on race
            plt.title('model loss for race classification')
        plt.ylabel('loss')
        plt.xlabel('epoch')
        plt.legend(['train', 'validation'], loc='upper left')
        plt.show()

        trainingloss=history.history['loss']
        validationloss=history.history['val_loss']

        print('final accuracy is %f' %results[1])
        confmatrix=sklearn.metrics.confusion_matrix(self.yvaltruth,predictions)
        print(confmatrix)
        return [trainingloss,validationloss,history,results,confmatrix]


    def cnn(self):
        print('init')
    def cnnhomebrew(self):
        print('init')
    def cnntwo(self):
        print('init')
    def vae(self):
        print('init')


#Pre-processing
PREPROCESS=preprocess()
#PREPROCESS.firsttimerun()
train_images,train_labels,val_images,val_labels,categories=PREPROCESS.runeverytime()

# Task 1, FCNN
NETWORKS=networks(tasknum=1,xtrain=train_images,ytrain=train_labels,xval=val_images,yval=val_labels,categories=categories)
FCNN=NETWORKS.fcnn()
## Task 2, CNN
CNN=NETWORKS.cnn()
## Task 3, homebrew CNN
CNNHOMEBREW=NETWORKS.cnnhomebrew()
## Task 4, multitask CNN
CNNTWO=NETWORKS.cnntwo()
## Task 5, Variational Auto-Encoder
VAE=NETWORKS.vae()
