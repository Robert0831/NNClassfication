Train model,use [train2.txt](https://github.com/Robert0831/NNClassfication/blob/main/train2.txt) data ,it is shuffled training set ,and you need to put the data in the folder [images](https://github.com/Robert0831/NNClassfication/tree/main/image)
----------------------------------------------------------------------------

To train two-layer model ,directly execution [fnn.py](https://github.com/Robert0831/NNClassfication/blob/main/fnn.py)

To train LeNet5 ,directly execution [Lenet.py](https://github.com/Robert0831/NNClassfication/blob/main/Lenet.py)

To train Improved LeNet5 ,directly execution [NLenet.py](https://github.com/Robert0831/NNClassfication/blob/main/NLenet.py)
----------------------------------------------------------------------------
Testing

To test three model directly execution [test.py](https://github.com/Robert0831/NNClassfication/blob/main/test.py)
----------------------------------------------------------------------------
Pretrain model 

two-layer:[weights.pkl](https://github.com/Robert0831/NNClassfication/blob/main/weights.pkl)

LeNet5:[Lanet_weights.pkl](https://github.com/Robert0831/NNClassfication/blob/main/weights.pkl)

Improved LeNet5:[NLanet_weights.pkl](https://github.com/Robert0831/NNClassfication/blob/main/weights.pkl)

if want to load pretrain model,there have be a line is  EX.model=LeNet5(weights="pretrain model flie name") 
