import pickle
import random
import numpy as np
import matplotlib.pyplot as plt
from abc import ABCMeta, abstractmethod
import os
import cv2
import pandas as pd
#讀pretrain model
def load():
    with open("mnist.pkl",'rb') as f:
        mnist = pickle.load(f)
    return mnist["training_images"], mnist["training_labels"], mnist["test_images"], mnist["test_labels"]
#維度改變
def MakeOneHot(Y, D_out):
    N = Y.shape[0]
    Z = np.zeros((N, D_out))
    Z[np.arange(N), Y] = 1
    return Z

#Fully connected layer
class FC():
    """
    Fully connected layer
    """
    def __init__(self, D_in, D_out):
        #print("Build FC")
        self.cache = None
        #self.W = {'val': np.random.randn(D_in, D_out), 'grad': 0}
        self.W = {'val': np.random.normal(0.0, np.sqrt(2/D_in), (D_in,D_out)), 'grad': 0}
        self.b = {'val': np.random.randn(D_out), 'grad': 0}

    def _forward(self, X):
        #print("FC: _forward")
        out = np.dot(X, self.W['val']) + self.b['val']
        self.cache = X
        return out

    def _backward(self, dout):
        #print("FC: _backward")
        X = self.cache
        dX = np.dot(dout, self.W['val'].T).reshape(X.shape)
        self.W['grad'] = np.dot(X.reshape(X.shape[0], np.prod(X.shape[1:])).T, dout)
        self.b['grad'] = np.sum(dout, axis=0)
        #self._update_params()
        return dX

    def _update_params(self, lr=0.001):
        # Update the parameters
        self.W['val'] -= lr*self.W['grad']
        self.b['val'] -= lr*self.b['grad']

class ReLU():
    """
    ReLU activation layer
    """
    def __init__(self):
        #print("Build ReLU")
        self.cache = None

    def _forward(self, X):
        #print("ReLU: _forward")
        out = np.maximum(0, X)
        self.cache = X
        return out

    def _backward(self, dout):
        #print("ReLU: _backward")
        X = self.cache
        dX = np.array(dout, copy=True)
        dX[X <= 0] = 0
        return dX

class tanh():
    """
    tanh activation layer
    """
    def __init__(self):
        self.cache = X

    def _forward(self, X):
        self.cache = X
        return np.tanh(X)

    def _backward(self, X):
        X = self.cache
        dX = dout*(1 - np.tanh(X)**2)
        return dX

class Sigmoid():
    """
    Sigmoid activation layer
    """
    def __init__(self):
        self.cache = None

    def _forward(self, X):
        self.cache = X
        return 1 / (1 + np.exp(-X))

    def _backward(self, dout):
        X = self.cache
        X=1 / (1 + np.exp(-X))
        dX = dout*X*(1-X)
        return dX


class Softmax():
    """
    Softmax activation layer
    """
    def __init__(self):
        #print("Build Softmax")
        self.cache = None

    def _forward(self, X):
        #print("Softmax: _forward")
        maxes = np.amax(X, axis=1)
        maxes = maxes.reshape(maxes.shape[0], 1)
        Y = np.exp(X - maxes)
        Z = Y / np.sum(Y, axis=1).reshape(Y.shape[0], 1)
        self.cache = (X, Y, Z)
        return Z # distribution

    def _backward(self, dout):
        X, Y, Z = self.cache
        dZ = np.zeros(X.shape)
        dY = np.zeros(X.shape)
        dX = np.zeros(X.shape)
        N = X.shape[0]
        for n in range(N):
            i = np.argmax(Z[n])
            dZ[n,:] = np.diag(Z[n]) - np.outer(Z[n],Z[n])
            M = np.zeros((N,N))
            M[:,i] = 1
            dY[n,:] = np.eye(N) - M
        dX = np.dot(dout,dZ)
        dX = np.dot(dX,dY)
        return dX

#CNN
class Conv():
    """
    Conv layer
    """
    def __init__(self, Cin, Cout, F, stride=1, padding=0, bias=True):
        self.Cin = Cin
        self.Cout = Cout
        self.F = F
        self.S = stride
        #self.W = {'val': np.random.randn(Cout, Cin, F, F), 'grad': 0}
        self.W = {'val': np.random.normal(0.0,np.sqrt(2/Cin),(Cout,Cin,F,F)), 'grad': 0} # Xavier Initialization
        self.b = {'val': np.random.randn(Cout), 'grad': 0}
        self.cache = None
        self.pad = padding

    def _forward(self, X):
        X = np.pad(X, ((0,0),(0,0),(self.pad,self.pad),(self.pad,self.pad)), 'constant')
        (N, Cin, H, W) = X.shape
        H_ = H - self.F + 1
        W_ = W - self.F + 1
        Y = np.zeros((N, self.Cout, H_, W_))

        for n in range(N):
            for c in range(self.Cout):
                for h in range(H_):
                    for w in range(W_):
                        Y[n, c, h, w] = np.sum(X[n, :, h:h+self.F, w:w+self.F] * self.W['val'][c, :, :, :]) + self.b['val'][c]

        self.cache = X
        return Y

    def _backward(self, dout):
        # dout (N,Cout,H_,W_)
        # W (Cout, Cin, F, F)
        X = self.cache
        (N, Cin, H, W) = X.shape
        H_ = H - self.F + 1
        W_ = W - self.F + 1
        W_rot = np.rot90(np.rot90(self.W['val']))

        dX = np.zeros(X.shape)
        dW = np.zeros(self.W['val'].shape)
        db = np.zeros(self.b['val'].shape)

        # dW
        for co in range(self.Cout):
            for ci in range(Cin):
                for h in range(self.F):
                    for w in range(self.F):
                        dW[co, ci, h, w] = np.sum(X[:,ci,h:h+H_,w:w+W_] * dout[:,co,:,:])

        # db
        for co in range(self.Cout):
            db[co] = np.sum(dout[:,co,:,:])

        dout_pad = np.pad(dout, ((0,0),(0,0),(self.F,self.F),(self.F,self.F)), 'constant')
        #print("dout_pad.shape: " + str(dout_pad.shape))
        # dX
        for n in range(N):
            for ci in range(Cin):
                for h in range(H):
                    for w in range(W):
                        #print("self.F.shape: %s", self.F)
                        #print("%s, W_rot[:,ci,:,:].shape: %s, dout_pad[n,:,h:h+self.F,w:w+self.F].shape: %s" % ((n,ci,h,w),W_rot[:,ci,:,:].shape, dout_pad[n,:,h:h+self.F,w:w+self.F].shape))
                        dX[n, ci, h, w] = np.sum(W_rot[:,ci,:,:] * dout_pad[n, :, h:h+self.F,w:w+self.F])

        return dX

class MaxPool():
    def __init__(self, F, stride):
        self.F = F
        self.S = stride
        self.cache = None

    def _forward(self, X):
        # X: (N, Cin, H, W): maxpool along 3rd, 4th dim
        (N,Cin,H,W) = X.shape
        F = self.F
        W_ = int(float(W)/F)
        H_ = int(float(H)/F)
        Y = np.zeros((N,Cin,W_,H_))
        M = np.zeros(X.shape) # mask
        for n in range(N):
            for cin in range(Cin):
                for w_ in range(W_):
                    for h_ in range(H_):
                        Y[n,cin,w_,h_] = np.max(X[n,cin,F*w_:F*(w_+1),F*h_:F*(h_+1)])
                        i,j = np.unravel_index(X[n,cin,F*w_:F*(w_+1),F*h_:F*(h_+1)].argmax(), (F,F))
                        M[n,cin,F*w_+i,F*h_+j] = 1
        self.cache = M
        return Y
    #可能會有奇數的情形,用補0解決
    def _backward(self, dout):
        M = self.cache
        (N,Cin,H,W) = M.shape
        dout = np.array(dout)
        (a1,a2,a3,a4)=dout.shape
        #print("dout.shape: %s, M.shape: %s" % (dout.shape, M.shape))
        if a3*2!=H:
            dX = np.zeros((N,Cin,H-1,W-1))
            dXX=np.zeros((N,Cin,H,W))
            for n in range(N):
                for c in range(Cin):
                    #print("(n,c): (%s,%s)" % (n,c))
                    dX[n,c,:,:] = dout[n,c,:,:].repeat(2, axis=0).repeat(2, axis=1)
            dXX[:,:,:-1,:-1]=dX
            return dXX*M
        
        else:
            dX = np.zeros(M.shape)
            for n in range(N):
                for c in range(Cin):
                    #print("(n,c): (%s,%s)" % (n,c))
                    dX[n,c,:,:] = dout[n,c,:,:].repeat(2, axis=0).repeat(2, axis=1)
            return dX*M
        
class CrossEntropyLoss():
    def __init__(self):
        pass

    def get(self, Y_pred, Y_true):
        N = Y_pred.shape[0]
        softmax = Softmax()
        prob = softmax._forward(Y_pred)
        #loss = NLLLoss(prob, Y_true)
        Y_serial = np.argmax(Y_true, axis=1)
        dout = prob.copy()
        dout[np.arange(N), Y_serial] -= 1
        #return loss, dout
        return dout
    
class Net(metaclass=ABCMeta):
    # Neural network super class

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def forward(self, X):
        pass

    @abstractmethod
    def backward(self, dout):
        pass

    @abstractmethod
    def get_params(self):
        pass

    @abstractmethod
    def set_params(self, params):
        pass

class LeNet5(Net):
    # LeNet5

    def __init__(self,weights=''):
        self.conv1 = Conv(3, 6, 5)#64->60
        self.sig1 = Sigmoid()
        self.pool1 = MaxPool(2,2) #60->30
        self.conv2 = Conv(6, 16, 5) #30->26
        self.sig2 = Sigmoid()
        self.pool2 = MaxPool(2,2) #26->13
        self.conv3=  Conv(16, 120, 5) #13->9

        self.FC1 = FC(120*9*9, 84)
        self.sig3 = Sigmoid()
        self.FC2 = FC(84, 50)
        self.Softmax = Softmax()
        if weights == '':
            pass
        else:
            with open(weights,'rb') as f:
                params = pickle.load(f)
                self.set_params(params)
        self.p2_shape = None

    def forward(self, X):
        h1 = self.conv1._forward(X)
        a1 = self.sig1._forward(h1)
        p1 = self.pool1._forward(a1)
        h2 = self.conv2._forward(p1)
        a2 = self.sig2._forward(h2)
        p2 = self.pool2._forward(a2)
        h3=self.conv3._forward(p2)

        self.p3_shape = h3.shape        #back會用到
        fl = h3.reshape(X.shape[0],-1) # Flatten (batch,其他)
        h4 = self.FC1._forward(fl)
        a4 = self.sig3._forward(h4)
        h5 = self.FC2._forward(a4)
        a5 = self.Softmax._forward(h5)
        return a5

    def backward(self, dout):
        dout = self.FC2._backward(dout)
        dout = self.sig3._backward(dout)
        dout = self.FC1._backward(dout)

        dout = dout.reshape(self.p3_shape) # reshape
        dout=self.conv3._backward(dout)
        dout = self.pool2._backward(dout)
        dout = self.sig2._backward(dout)
        dout = self.conv2._backward(dout)
        dout = self.pool1._backward(dout)
        dout = self.sig1._backward(dout)
        dout = self.conv1._backward(dout)

    def get_params(self):
        return [self.conv1.W, self.conv1.b, self.conv2.W, self.conv2.b, self.conv3.W, self.conv3.b,self.FC1.W, self.FC1.b, self.FC2.W, self.FC2.b]

    def set_params(self, params):
        [self.conv1.W, self.conv1.b, self.conv2.W, self.conv2.b, self.conv3.W, self.conv3.b,self.FC1.W, self.FC1.b, self.FC2.W, self.FC2.b] = params

class SGD():
    def __init__(self, params, lr=0.001, reg=0):
        self.parameters = params
        self.lr = lr
        self.reg = reg

    def step(self):
        for param in self.parameters:
            param['val'] -= (self.lr*param['grad'] + self.reg*param['val'])

class SGDMomentum():
    def __init__(self, params, lr=0.001, momentum=0.99, reg=0):
        self.l = len(params)
        self.parameters = params
        self.velocities = []
        for param in self.parameters:
            self.velocities.append(np.zeros(param['val'].shape))
        self.lr = lr
        self.rho = momentum
        self.reg = reg

    def step(self):
        for i in range(self.l):
            self.velocities[i] = self.rho*self.velocities[i] + (1-self.rho)*self.parameters[i]['grad']
            self.parameters[i]['val'] -= (self.lr*self.velocities[i] + self.reg*self.parameters[i]['val'])


#取batch
def getimg(set,idx):
    images=[]
    for i in range(5):
        img=set['dir'][int(idx+i)]
        img = cv2.imread(img)
        img = cv2.resize(img, (64, 64))
        img=img/255
        img=img.transpose(2,0,1)
        images.append(img)
    return np.array(images)
def getlabel(set,idx):
    labels=[]
    for i in range(5):
        labels.append(set['class'][int(idx+i)])
    return np.array(labels)


model=LeNet5()
datapath=os.path.join(os.path.abspath(""),'train2.txt')
dataset=pd.read_csv(datapath,sep=" ",header=None,names=["dir", "class"])

valpath=os.path.join(os.path.abspath(""),'val.txt')
valset=pd.read_csv(valpath,sep=" ",header=None,names=["dir", "class"])

optim = SGDMomentum(model.get_params(), lr=0.0001, momentum=0.80, reg=0.00003)
criterion = CrossEntropyLoss()



    
totalt=len(dataset)
totalv=len(valset)
for epoch in range(0,10):
    tt1s=0
    vt1s=0
    for idx in range(0,len(dataset),5):

        img=getimg(dataset,idx)
        label=getlabel(dataset,idx)
        label=MakeOneHot(label,50)
        Y_pred = model.forward(img)
        #dout = criterion.get(Y_pred,label)
        #先算到softmax的back
        dout=Y_pred-label
        model.backward(dout)
        optim.step()
        print(f'epoch:{epoch} idx:{idx}')
        weights = model.get_params()
        with open("Lanet_weights_"+str(epoch)+".pkl","wb") as f:
            pickle.dump(weights, f)


    #count score
        out=np.argmax(Y_pred,1)
        label=np.argmax(label,1)
        for j in range(out.shape[0]):
            if out[j]==label[j]:
                tt1s+=1


    #val
    for iv in range(0,len(valset),5):
        imgv=getimg(valset,iv)
        labelv=getlabel(valset,iv)
        labelv=MakeOneHot(labelv,50)
        Y_predv = model.forward(imgv)
        outv=np.argmax(Y_predv,1)
        labelv=np.argmax(labelv,1)
        for j in range(outv.shape[0]):
            if outv[j]==labelv[j]:
                vt1s+=1


    print(f'Epoch:{epoch} ; Training top-1 accuracy:{round(tt1s/totalt,5)}') 
    logger = open('Lanet5_score.txt', 'a')
    logger.write('%f %f\n'%(round(tt1s/totalt,5),round(vt1s/totalv,5)))
    logger.close()
