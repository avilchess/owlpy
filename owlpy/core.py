'''--------------------------- Core Script ---------------------------------'''
'''
    Description: This library is based on the algorithms described in 
    [1] Chin-Chia Michael Yeh, Yan Zhu, Liudmila Ulanova, Nurjahan Begum, 
        Yifei Ding, Hoang Anh Dau, Diego Furtado Silva, Abdullah Mueen, 
        Eamonn Keogh (2016). Matrix Profile I: All Pairs Similarity Joins 
        for Time Series: A Unifying View that Includes Motifs, Discords and 
        Shapelets. IEEE ICDM 2016.
'''
import numpy as np
import pandas as pd
import time

import matplotlib.pyplot as plt

def slidingDotProduct(Q, T):
    n = len(T)
    m = len(Q)

    Ta = list(T) # Copy the T without modifying the original
    [Ta.append(0) for i in range(0, n)]
    
    Qr = Q[::-1]
    
    Qra = list(Qr) # Copy the T without modifying the original
    [Qra.append(0) for i in range(0, 2*n - m)]
    
    Qraf = np.fft.fft(Qra)
    Taf = np.fft.fft(Ta)
    
    QT = np.fft.ifft(np.multiply(Qraf, Taf))
    return QT[m:n]
    
def calculateDistanceProfile(QT, Q, T, sumT, sumT2, sumQ, sumQ2, meanT, meanT_2, sigmaT, sigmaT2):
    n = len(T)
    m = len(Q)

    # computing the distances -- O(n) time.

    a = [(sumT2[i] - 2*sumT[i]*meanT[i] + m*meanT_2[i])/sigmaT2[i] for i in range(0, n - m)]
    b = [-2*(QT[i] - sumQ*meanT[i])/sigmaT[i] for i in range(0, n - m)]
    c = sumQ2
    dist = [a[i] + b[i] + c for i in range(0, n - m)]
    D = np.abs(np.sqrt(dist))
    return D

# The code below takes O(m) for each subsequence
# you should replace it for MASS
def computeMeanStd(Q, T):
    n = len(T)
    m = len(Q)

    # Compute Q stats -- O(n)
    sumQ = np.sum(Q)
    sumQ2 = np.sum(np.power(Q, 2))

    # Compute T stats -- O(n)
    cum_sumT = np.cumsum(T, dtype=float)
    cum_sumT2 = np.cumsum(np.power(T, 2), dtype=float)
    sumT2 = [cum_sumT2[i + m] - cum_sumT2[i] for i in range(0, n - m)]
    sumT = [cum_sumT[i + m] - cum_sumT[i] for i in range(0, n - m)]
    meanT = [sumT[i]/m for i in range(0, n - m)]
    meanT2 = [sumT2[i]/m for i in range(0, n - m)]
    meanT_2 = np.power(meanT, 2)
    sigmaT2 = [meanT2[i] - meanT_2[i] for i in range(0,n - m)]
    sigmaT = np.sqrt(sigmaT2)
    
    return sumT, sumT2, sumQ, sumQ2, meanT, meanT_2, sigmaT, sigmaT2
    
# MUEEN’S ALGORITHM FOR SIMILARITY SEARCH (MASS)
def mass(Q, T):
    if np.std(Q)!=0:
        Q = (Q -np.mean(Q))/np.std(Q)
    QT = slidingDotProduct(Q, T)
    sumT, sumT2, sumQ, sumQ2, meanT, meanT_2, sigmaT, sigmaT2 = computeMeanStd(Q, T)
    D = calculateDistanceProfile(QT, Q, T, sumT, sumT2, sumQ, sumQ2, meanT, meanT_2, sigmaT, sigmaT2)
    
    return D

def elementWiseMin(Pab, Iab, D, idx,ignore_trivial,m):

    Pab_copy = [1000000 for i in range(0, len(Pab))]
    flag = False

    for i in range(0, len(D)):
        if not ignore_trivial or (np.abs(idx-i)>m):
            if (Pab[i] == float('Inf')):
                Pab_copy[i] = D[i]
                Iab[i] = idx
                flag = True
            elif (D[i] < Pab[i]):
                Pab[i] = D[i]
                Iab[i] = idx

    if flag:
        return Pab_copy, Iab
    else:
        return Pab, Iab
    
    

def stamp(Ta, Tb, m):
    nb = len(Tb)
    na = len(Ta)
    Pab = [float('Inf') for i in range(0, na - m)]
    Iab = [0 for i in range(0, na - m)]
    idxes = range(0, nb - m)
    
    for idx in idxes:
        D = mass(Tb[idx : idx + m], Ta)
        Pab, Iab = elementWiseMin(Pab, Iab, D, idx, ignore_trivial=(Ta==Tb).all(),m=m)
        
    return Pab, Iab

# Quick Test
def test_stamp(Ta, Tb, m):
    start_time = time.time()
    
        
    Pab, Iab = stamp(Ta, Tb, m)
    print("--- %s seconds ---" % (time.time() - start_time))
    
    plot_graphics(Ta,Tb,Pab, Iab,m)
    return Pab
    
def plot_graphics(Ta,Tb,values,indexes,m):
    fig_width = 16
    fig_height = 8
    fig_dpi = 100
    plt.figure(figsize=(fig_width, fig_height), dpi=fig_dpi)
    plt.subplot(411)
    plt.plot(Ta)
    plt.xlim((0,len(Tb)))

    plt.title('A')
    plt.subplot(412)
    plt.plot(Tb)
    plt.plot(range(np.argmax(values),np.argmax(values)+m),Tb[np.argmax(values):np.argmax(values)+m],c='r')

    plt.title('B')
    plt.xlim((0,len(Tb)))

    plt.subplot(413)
    plt.title('P_ab')
    plt.plot(range(0,len(values)), values, '#ff5722')
    plt.plot(np.argmax(values),np.max(values),marker='x',ms=10)
    plt.xlim((0,len(Tb)))
    plt.xlabel('Index')
    plt.ylabel('Value')
    plt.subplot(414)    
    plt.title('P_ab')
    plt.plot(range(0,len(indexes)), indexes, '#ff5722')
    plt.xlabel('Index')
    plt.ylabel('Value')
    plt.show()


