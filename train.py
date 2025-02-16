import helper

args = helper.get_train_args()
print(args)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sb

import torch
from torch import nn
from torch import optim
import torch.nn.functional as F
from torchvision import datasets, transforms

from PIL import Image

import model as Model

model = Model.model_factory(
    arch = args.arch,
    hidden_units = args.hidden_units,
    gpu = args.gpu,
    learningrate = args.learning_rate
    )

data_dir = args.data_directory
train_dir = data_dir + '/train'
valid_dir = data_dir + '/valid'
test_dir = data_dir + '/test'

train_transforms = transforms.Compose([transforms.RandomRotation(30),
                                       transforms.RandomResizedCrop(100),
                                       transforms.RandomHorizontalFlip(),
                                       helper.standard_transforms])


train_data = datasets.ImageFolder(train_dir, transform=train_transforms)
test_data = datasets.ImageFolder(test_dir, transform=helper.standard_transforms)
valid_data = datasets.ImageFolder(valid_dir, transform=helper.standard_transforms)


trainloader = torch.utils.data.DataLoader(train_data, batch_size=64, shuffle=True)
testloader = torch.utils.data.DataLoader(test_data, batch_size=32)
validloader = torch.utils.data.DataLoader(valid_data, batch_size=32)


model.class_to_idx =  train_data.class_to_idx

device = torch.device("cuda" if torch.cuda.is_available() and args.gpu else "cpu")

criterion = nn.NLLLoss()
optimizer = optim.Adam(model.classifier.parameters(), lr = model.settings["learningrate"])
model.to(device)

epochs = args.epochs
print_every = 20
steps = 0
current_epoch = model.settings["current_epoch"]

for e in range(current_epoch, epochs):
    running_loss = 0
    for images, labels in iter(trainloader):
        steps += 1
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        # Forward and backward passes
        output = model.forward(images)
        loss = criterion(output, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        
        print(f'Training epoch {e + 1}/{epochs}{"." * (steps % 4)}                    ', end = "\r")
              
        if steps % print_every == 0:
              
            print('Running validation...                           ', end = '\r')

            # Make sure network is in eval mode for inference
            model.eval()

            # Turn off gradients for validation, saves memory and computations
            with torch.no_grad():
                test_loss, accuracy = helper.validation(model, testloader, criterion, device)

            print("Epoch: {}/{}.. ".format(e+1, epochs),
                  "Training Loss: {:.3f}.. ".format(running_loss/print_every),
                  "Test Loss: {:.3f}.. ".format(test_loss/len(testloader)),
                  "Test Accuracy: {:.3f}".format(accuracy/len(testloader)),
                  "\n",
                  end = "\r")            
            running_loss = 0

            # Make sure training is back on
            model.train()
              
    model.settings["current_epoch"] = e

Model.save(model, optimizer, args.save_dir + "/checkpoint.pth")