#!/usr/bin/env python
# coding: utf-8

#live_wafer_fork_rev2_-detector-と内容同じで名前変更 rev3へ

# rev0cに対して
#捜索のスタート地点が既に255なら、そこで終わってしまうので、、スタート地点を上下にそれぞれ10ピクセルずつずらして、上下に捜索して合算する
#動作は重くなりそう

# rev1cに対して
# Waferの厚みも捜査型で出してみる。走査線は少なめに

# Binarization_rev3c_contourからの派生で、動画によるWafer厚み認識の味見評価

# rev4cとして、精度アップ策でお試し。Wafer Gapのピクセル値を取出して19.225で割るとpixel/mmが求まる。これに0.775を掛けると
# Wafer厚み"べき"相当のピクセル数が出る。

# coding: utf-8
import cv2
import numpy as np
from matplotlib import pyplot as plt
import time
import math
import sympy as sym
import sys
import numpy
import heapq

path = '/Users/021006/Documents/AIT/Python'
##C:\Users\021006\Documents\AIT\Python

# 対象物の厚さを設定する（mm） Waferなら0.775
# 今回はボートのピッチを既知として、8mmピッチのボートを使用
boat_pitch = 25
fork_thickness = 5
threshold = 200 #Default=200

cap = cv2.VideoCapture(0)
cap.set(4, 2000)  # Height
cap.set(3, 2000)  # Width

# 3:1200 (横) , 4:1000 (縦) とすると (720,1280) (縦,横)　となる
# 3:2000, 4:2000 とすると (1080,1920)となる
# 3:3000, 4:2000 とすると (2160,3840)となる
# 3:3000, 4:3000 とすると (3156,4224)となる

#検出枠の座標を設定
#rect_pt1 = (1800, 500)
#rect_pt2 = (2300, 1500)
#今回はForkを検出したいので、検出枠の幅を小さくする
#高さも、Wafer2枚分になるので小さくする
#検出枠を自動にするので、少し大きめにしておく
#Ref画像の大きさは360x240なので、同じ比率で倍ぐらいにしておく=> 720x480

#ref_pic_sizeの2倍の大きさにする
rect_pt1 = (1000, 510) #2000, 1020 : 2160/3840用
rect_pt2 = (1400, 750) #2800, 1500 : 2160/3840用
#以下はオリジナル
#rect_pt1 = (1780, 1020)
#rect_pt2 = (2500, 1500)
ref_pic_size = (400, 240)
denom = 30


#検出枠の色設定
rect_rgb = (255, 0, 255)
#類似検出枠の色設定
rect_rgb2 = (0, 255, 255)

#検出枠の大きさを取得しておく
rect_w = rect_pt2[0] - rect_pt1[0]
rect_h = rect_pt2[1] - rect_pt1[1]
# 検出枠座標を多次元配列化（あとで計算に使う）
#rect_pt1_3d = np.array([rect_pt1])

# リアルタイム値がばらつく対策で、測定X回分の平均値を表示するための箱作り
gap_upper_xave = []
gap_lower_xave = []
ave_len = 5  # 平均にするサンプル数。測定X回分のX値
gap_upper_xave_ave_list=[0.00]
gap_lower_xave_ave_list=[0.00]


#検出枠rect_pt1とrect_pt2の中から360:240の画像を抜き出すプログラム

#特徴点マッチングAKAZEを使用http://sh0122.hatenadiary.jp/entry/2017/11/23/180044
#https://qiita.com/hitomatagi/items/
#https://qiita.com/best_not_best/items/c9497ffb5240622ede01
def ref_detector():

    #類似度の数値箱
    ret_list = []
    width_rate_list = []
    height_rate_list = []

    # ref画像準備
    detector_ref = cv2.imread(path + '/ref_gray_th_200_frame_cut_3.png')
    # Ref画像との比較
    #detector = cv2.AKAZE_create()
    detector = cv2.ORB_create()

    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    (ref_kp, ref_des) = detector.detectAndCompute(detector_ref, None)

    for i in range(int(denom)):
        width_rate = ref_pic_size[0]/denom * i #ref画像の大きさの10分の1づつ進めて、画像を類似比較する。横に進む量をwidth_rateとした
        print('width_rate', width_rate)
        for j in range(int(denom)):
            try:
                height_rate = ref_pic_size[1]/denom * j #縦に進む量をheight_rateとした
                print('height_rate',height_rate)
                cut_position_y = rect_pt1[1] + int(height_rate)
                cut_position_x = rect_pt1[0] + int(width_rate)
                #検出枠の左上から縦横1コマすすめた状態からスタートする。このループでは、縦に1コマずつ進んで行く
                detector_cut = frame[cut_position_y:(cut_position_y+ref_pic_size[1]), cut_position_x:(cut_position_x+ref_pic_size[0])]
                #デバッグ用
                cv2.imshow('detector_cut', detector_cut)
                #グレースケールと二値化
                detector_cut_gray = cv2.cvtColor(detector_cut, cv2.COLOR_BGR2GRAY)
                # ある閾値で2値化し、白と黒に分ける
                ret, detector_comp = cv2.threshold(detector_cut_gray, threshold, 255, cv2.THRESH_BINARY)

                (comp_kp, comp_des) = detector.detectAndCompute(detector_comp, None)
                matches = bf.match(ref_des, comp_des)
                dist = [m.distance for m in matches]
                ret = sum(dist) / len(dist)
                ret_list.append(ret)
                width_rate_list.append(width_rate)
                height_rate_list.append(height_rate)
            except cv2.error:
                ret = 100000

    min_index = ret_list.index(min(ret_list))
    width_rate_min = width_rate_list[min_index]
    height_rate_min = height_rate_list[min_index]
    match_x_position = rect_pt1[0] + width_rate_min
    match_y_position = rect_pt1[1] + height_rate_min

    return int(match_x_position), int(match_y_position), int(width_rate_min), int(height_rate_min) #一番類似度の高いカットの左上の頂点座標を取得


#テンプレートマッチングを使用http://sh0122.hatenadiary.jp/entry/2017/11/23/180044
#http://labs.eecs.tottori-u.ac.jp/sd/Member/oyamada/OpenCV/html/py_tutorials/py_imgproc/py_template_matching/py_template_matching.html
def ref_detector_matchTemplate():
    # 類似度の数値箱
    ret_list = []
    width_rate_list = []
    height_rate_list = []

    # テンプレ画像準備
    template = cv2.imread(path + '/ref2_gray_th_200_frame_cut_4.png', 0)

    #捜索対象の画像準備。ここでは、切り取った枠内の捜索とする
    detector_target = frame[rect_pt1[1]:rect_pt2[1], rect_pt1[0]:rect_pt2[0]]
    im_gray = cv2.cvtColor(detector_target, cv2.COLOR_BGR2GRAY)
    img2 = im_gray.copy()

    w, h = template.shape[::-1]

    #6つのメソッドを比較する(比較結果、どれでも良さそう)
    methods = ['cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR',
               'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']
    meth1 = 'cv2.TM_CCOEFF'
    meth2 = 'cv2.TM_CCOEFF_NORMED'
    meth3 = 'cv2.TM_CCORR'
    meth4 = 'cv2.TM_CCORR_NORMED'
    meth5 = 'cv2.TM_SQDIFF'
    meth6 = 'cv2.TM_SQDIFF_NORMED'

    meth = meth1


    img = img2.copy()
    method = eval(meth)

    # Apply template Matching
    res = cv2.matchTemplate(img,template,method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    #デバッグ用
    #print('min_val, max_val, min_loc, max_loc', min_val, max_val, min_loc, max_loc)
    #time.sleep(5)

    # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
    if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        top_left = min_loc
    else:
        top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)

    match_x_position = rect_pt1[0] + top_left[0]
    match_y_position = rect_pt1[1] + top_left[1]

    return int(match_x_position), int(match_y_position), max_val



'''
    #デバッグ用

    cv2.rectangle(img, top_left, bottom_right, rect_rgb2, 3)
    plt.subplot(121), plt.imshow(res, cmap='gray')
    plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
    plt.subplot(122), plt.imshow(img, cmap='gray')
    plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
    plt.suptitle(meth)

    plt.show()

    time.sleep(60)
'''






# 関数化する

#引数の説明
#x_start_position: 上側のクリアランス測定時は box1_3_x と入力。下側のクリアランス測定時は box1_2_x と入力。
#x_offset: スタート位置を頂点からずらす量。ピクセル座標を正の整数で入力。
#y_offset: yの走査線をシフトさせて、上下に白(255)を探しに行く。上側のクリアランス測定時は負の整数を、下側は正の整数を入力。
#x_end_position: スタート位置と反対側の頂点のx座標。上側のクリアランス測定時は box1_4_x と入力。下側は box1_1_x と入力。
#y_shift: 上側に捜索時は -1 と入力、下側に捜索時は 1 と入力。
#x_shift: 次の操作位置へのシフト量で正の整数を入力
#xy_list: 上部を上側に捜索ならgap_upper_up、上部を下側に捜索ならgap_upper_down、下部を上側に捜索ならgap_lower_up、下側を下側に捜索ならgap_lower_down
#a(傾き),b(切片): a_mid_lower, b_mid_lower, a_mid_upper, b_mid_upper, a_top_lower, b_top_lower, a_btm_upper, b_btm_upperから選ぶ
#a_inv: a_mid_lower_inv, a_mid_upper_inv, a_top_lower_inv, a_btm_upper_invから選ぶ

def gap_detector(x_start_position,x_offset_start,x_offset_end,y_offset,x_end_position,y_shift,x_shift,xy_list,a,b,a_inv): #y_shiftは上に捜索時は負の値
    # ##### Fork上辺から上部Waferへの距離測定 #####
    # スタートは左の頂点から
    x_start = x_start_position + x_offset_start  # スタート地点x座標。x_offset分内側からスタート
    y_start = a * x_start + b + y_offset # yスタート座標をy_offset分シフト

    print('x_start230',x_start)
    print('y_start231',y_start)

    # スタート地点から、反対側の頂点x -150ピクセルまで、ある一定の間隔で上下へのオブジェクト捜索を繰り返していく
    i = 0
    while x_start < x_end_position - x_offset_end:  # エッジを避けるためx_offset分内側で終わる
        b_inv = y_start - a_inv * x_start  # 垂直線invの切片bを求める
        x_next = (y_start - b_inv) / a_inv  # x座標を求める
        org_x_start = x_next  # スタート位置のx座標を記憶しておく
        org_y_start = y_start  # スタート位置のy座標を記憶しておく


        # 白いオブジェクトにあたるまでループ
        if y_start <=240: # index out of range （画像サイズをはみ出している）となるので、条件分岐

            while th3[int(y_start), int(x_next)] <= 255:
                # 255より小さい（⇒2値化しているので、白を意味する）時、if以下実行
                if th3[int(y_start), int(x_next)] < 255:
                    # yを1ピクセル上に移動
                    y_start += y_shift  # 画像上ではyは下に行くほどプラス、上に行くほどマイナス
                    # その時のx座標を求める
                    x_next = (y_start - b_inv) / a_inv
                    # y座標が2未満になったら捜索ストップ
                    if y_start < 6:
                        # print('y_start_upper_n10 cannot be negative value!!!')
                        print('break 248')
                        break
                    # y座標が画角-2よりも大きくなったら捜索ストップ
                    elif y_start > ref_pic_size[1] -6:
                        print('break 252')
                        break
                    # x座標が2未満になったら捜索ストップ
                    elif x_next < 6:
                        print('break 256')
                        # print('x_next cannot be negative value!!!')
                        break
                    # x座標がフレームサイズを超えたら捜索ストップ
                    elif x_next > ref_pic_size[0] - 6:
                        print('break 261')
                        # print('x_next cannot be more than max width!!!')
                        break
                # 255の時（⇒2値化しているので、白を意味する）時、elif以下実行
                elif th3[int(y_start), int(x_next)] == 255:
                    # 白を見つけた位置のy座標を記録する
                    y_255_position = y_start
                    # 白を見つけた位置のx座標を記録する
                    x_255_position = x_next
                    # スタート地点のx,y座標と、白を見つけた一のx,y座標から、以下式で2点間距離を計算する
                    xy_list.append(
                        np.sqrt((org_x_start - x_255_position) ** 2 + (org_y_start - y_255_position) ** 2))

                    # print('上辺から上部へのクリアランス測定,上側に捜索中')
                    # 捜索線を描く
                    cv2.line(frame, (int(org_x_start) + position_match[0], int(org_y_start) + position_match[1]),
                             (int(x_255_position) + position_match[0], int(y_255_position) + position_match[1]), (0, 150, 255), thickness=3)
                    break
                # y座標が1未満になったらループ終了
                elif y_start < 1:
                    print('break286')
                    break
        else:
            print('break289')
            break #このBreakが発動したらどうなっちゃうのか未確認
        # 次のループへの準備で、スタート地点をx_shift分右に移動する
        x_start += x_shift

        # その時のy座標も計算しておく
        y_start = a * x_start + b + y_offset
        i += 1
        # time.sleep(1)




#wafer間のピクセル数測定はとりあえず関数化するけど、引数無し
def gap_wafer2wafer():
    # ##### 下部Wafer上辺から上部Waferへの距離測定 #####
    # スタートは下のWaferの左の頂点から
    x_start_upper = box0_3_x + 60  # スタート地点x座標。100ピクセル内側から始める
    y_start_upper = a_btm_upper * x_start_upper + b_btm_upper  # スタート地点y座標


    # スタート地点から、反対側の頂点x -100ピクセルまで、ある一定の間隔で上下へのオブジェクト捜索を繰り返していく
    # print('LOOP START')
    #print('gap_wafers1')
    i = 0
    # #####上側に捜索 #####
    while x_start_upper < box0_4_x - 60:  # エッジを避けるため100ピクセル内側で終わる
        b_btm_upper_inv = y_start_upper - a_btm_upper_inv * x_start_upper  # 垂直線のbを求める
        # print('b_inv', b_inv)
        # print('a_inv', a_inv)
        x_next = (y_start_upper - b_btm_upper_inv) / a_btm_upper_inv  # x座標を求める
        org_x_start_upper = x_next  # スタート位置のx座標を記憶しておく
        org_y_start_upper = y_start_upper  # スタート位置のy座標を記憶しておく
        # 白いオブジェクトにあたるまでループ

        #print('gap_wafers2')
        print(int(y_start_upper),int(a_top_upper * x_start_upper + b_top_upper))
        print(x_start_upper, x_next)
        while int(y_start_upper) >= int(a_top_upper * x_start_upper + b_top_upper):#yの数値が大きい⇒下
            #print('gap_wafers3')
            # 255より小さい（⇒2値化しているので、黒を意味する）時、if以下実行
            if int(y_start_upper) > int(a_top_upper * x_start_upper + b_top_upper):
                #print('gap_wafers4')
                # yを1ピクセル上に移動
                y_start_upper -= 1  # 画像上ではyは下に行くほどプラス、上に行くほどマイナス
                # その時のx座標を求める
                x_next = (y_start_upper - b_btm_upper_inv) / a_btm_upper_inv
                # y座標が0未満になったら捜索ストップ
                if y_start_upper < 5:
                    #print('gap_wafers5')
                    # print('y_start_upper_n10 cannot be negative value!!!')
                    break
                # x座標が0未満になったら捜索ストップ
                elif x_next < 0:
                    #print('gap_wafers6')
                    print('x_next cannot be negative value!!!')
                    break
                # x座標がフレームサイズを超えたら捜索ストップ
                elif x_next > ref_pic_size[0] - 21:
                    #print('gap_wafers7')
                    print('x_next cannot be more than max width!!!')
                    break
            # 255の時（⇒2値化しているので、白を意味する）時、elif以下実行
            elif int(y_start_upper) == int(a_top_upper * x_start_upper + b_top_upper):
                #print('gap_wafers8')
                # 白を見つけた位置のy座標を記録する
                y_upper_255 = y_start_upper
                # 白を見つけた位置のx座標を記録する
                x_upper_255 = x_next
                # スタート地点のx,y座標と、白を見つけた一のx,y座標から、以下式で2点間距離を計算する
                gap_wafers.append(
                    np.sqrt((org_x_start_upper - x_upper_255) ** 2 + (org_y_start_upper - y_upper_255) ** 2))
                # print('org_x_start_upper', org_x_start_upper)
                # print('org_y_start_upper', org_y_start_upper)
                # print('x_upper_255', x_upper_255)
                # print('y_upper_255', y_upper_255)
                # print('上辺から上部へのクリアランス測定,上側に捜索中')
                # 捜索線を描く
                cv2.line(frame, (int(org_x_start_upper) + position_match[0], int(org_y_start_upper) + position_match[1]),
                         (int(x_upper_255) + position_match[0], int(y_upper_255) + position_match[1]), (0, 150, 150), thickness=3)
                break
            # y座標が1未満になったらループ終了
            elif y_start_upper < 1:
                print('gap_wafers9')
                print('break')
                break
        # print('gap_upper_up', gap_upper_up)
        # 次のループへの準備で、スタート地点を100ピクセル右に移動する
        x_start_upper += 20
        # print('looping....')
        # print('x_start_upper:', x_start_upper)
        # その時のy座標も計算しておく
        y_start_upper = a_btm_upper * x_start_upper + b_btm_upper
        i += 1
        # time.sleep(1)


while True:
    ret, frame = cap.read()  # 撮影開始

    #検出器を動かして、最も類似度の高いカットの左上頂点の座標を得る
    #position_match = ref_detector()[0:2]
    #テンプレートマッチング用
    position_match = ref_detector_matchTemplate()[0:2]
    max_val = ref_detector_matchTemplate()[2]

    #切り取った枠内での座標
    position_match_local = (int(position_match[0]-rect_pt1[0]),int(position_match[1]-rect_pt1[1]) )
    #デバッグ用
    print('position_match,position_match_local',position_match,position_match_local)

    # frameから指定座標で画像をカットし表示する
    frame_cut = frame[rect_pt1[1]:rect_pt2[1], rect_pt1[0]:rect_pt2[0]]
    # 画面からはみ出るので、表示サイズを小さくする（解像度は変えない）
    resized_frame_cut = cv2.resize(frame_cut, (int((rect_pt2[0]-rect_pt1[0]) / 2), int((rect_pt2[1]-rect_pt1[1]) / 2)))
    # リサイズしたフレームを表示する
    #デバッグ用
    #print('type:position_match_local',type(position_match_local))
    #print('type:position_match_local[0]',type(position_match_local[0]))
    #print('type:rect_rgb',type(rect_rgb))
    #print('type:rect_rgb2', type(rect_rgb2))
    rect1_pos_start = (int(position_match_local[0]/2),int(position_match_local[1]/2))
    rect1_pos_end = (int((position_match_local[0] + ref_pic_size[0])/2), int((position_match_local[1] + ref_pic_size[1])/2))
    # デバッグ用
    #print('type:rect1_pos_start',type(rect1_pos_start), rect1_pos_start)
    #print('type:rect1_pos_end',type(rect1_pos_end),rect1_pos_end)

    cv2.rectangle(resized_frame_cut, rect1_pos_start, rect1_pos_end, rect_rgb2, 3)

    cv2.imshow('resized_frame_cut', resized_frame_cut)

    #デバッグ用
    #time.sleep(5)

    # frameから指定座標で画像をカットし表示する
    detected_frame_cut = frame[int(position_match[1]):int(position_match[1]+ref_pic_size[1]), int(position_match[0]):int(position_match[0]+ref_pic_size[0])]
    # 画面からはみ出るので、表示サイズを小さくする（解像度は変えない）
    resized_detected_frame_cut = cv2.resize(frame_cut, (int(ref_pic_size[0]/ 3), int(ref_pic_size[1] / 3)))
    # リサイズしたフレームを表示する
    #cv2.imshow('resized_detected_frame_cut', resized_detected_frame_cut)



    # グレースケールで読み込む
    im_gray = cv2.cvtColor(detected_frame_cut, cv2.COLOR_BGR2GRAY)

    #大津2値化フィルター
    ret, th3 = cv2.threshold(im_gray, 0, 255, cv2.THRESH_OTSU)
    # ある閾値で2値化し、白と黒に分ける
    #ret, th3 = cv2.threshold(im_gray, threshold, 255, cv2.THRESH_BINARY)
    # フレームサイズを取得する（あとで使う）
    frame_height = frame.shape[0]
    frame_width = frame.shape[1]
    print('frame size: ',frame.shape)
    print('cut frame size: ',frame_cut.shape)
    # Contour（等高線）の数を数える
    contours, hierarchy = cv2.findContours(th3, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # 検出枠を描写
    cv2.rectangle(frame, rect_pt1, rect_pt2, rect_rgb, 5)

    cv2.rectangle(frame, position_match, (int(position_match[0]+ref_pic_size[0]), int(position_match[1]+ref_pic_size[1])), rect_rgb2, 5)

    #resized_th3 = cv2.resize(th3, (int((ref_pic_size[0] / 3)), int(ref_pic_size[1] / 3)))
    resized_th3 = cv2.resize(th3, (int((ref_pic_size[0]) / 1.5), int(ref_pic_size[1] / 1.5)))
    cv2.imshow('resized_th3', resized_th3)

    #デバッグ用
    print('len(contours)',len(contours))

    # Contourが3つの時だけ動作するようにしていたが、これだとなかなか動作しないので、面積が大きいbest3を抽出して動作させることにする
    # バグがあったので。3つ以上の時に動作するようにする
    # 類似度も条件に追加。一定の類似度以上で動作するように
    if len(contours) >= 3 and max_val >100000000:
        time.sleep(0.01)
        if len(contours) >= 3:
            #contour面積ベスト3のindex番号を求める
            contour_area = []
            for i, cnt in enumerate(contours):
                area = cv2.contourArea(cnt)
                contour_area.append(area)
            coutour_area_largest_3 = heapq.nlargest(3,contour_area) #ベスト3を抜き出す

            contour_area_1st_index = contour_area.index(coutour_area_largest_3[0]) #ベスト3のそれぞれのindex番号を求める
            contour_area_2nd_index = contour_area.index(coutour_area_largest_3[1])
            contour_area_3rd_index = contour_area.index(coutour_area_largest_3[2])

            #それぞれの頂点座標1つを求める
            contour_area_loc = []
            contour_area_1st_loc = np.int0(cv2.boxPoints(cv2.minAreaRect(contours[contour_area_1st_index])))
            contour_area_2nd_loc = np.int0(cv2.boxPoints(cv2.minAreaRect(contours[contour_area_2nd_index])))
            contour_area_3rd_loc = np.int0(cv2.boxPoints(cv2.minAreaRect(contours[contour_area_3rd_index])))
            contour_area_loc.append(contour_area_1st_loc[0,1])
            contour_area_loc.append(contour_area_2nd_loc[0,1])
            contour_area_loc.append(contour_area_3rd_loc[0,1])

            #頂点座標　数値が小さい順(画像上ではより上部に位置する)に並べる
            contour_area_loc_sort_from_top = heapq.nsmallest(3, contour_area_loc)

            top_contour_index = contour_area_loc.index(contour_area_loc_sort_from_top[0])
            middle_contour_index = contour_area_loc.index(contour_area_loc_sort_from_top[1])
            bottom_contour_index = contour_area_loc.index(contour_area_loc_sort_from_top[2])

            if top_contour_index ==0 and middle_contour_index ==1 and bottom_contour_index ==2:
                top_contour_index = contour_area_1st_index
                middle_contour_index = contour_area_2nd_index
                bottom_contour_index = contour_area_3rd_index

            elif top_contour_index ==0 and middle_contour_index ==2 and bottom_contour_index ==1:
                top_contour_index = contour_area_1st_index
                middle_contour_index = contour_area_3rd_index
                bottom_contour_index = contour_area_2nd_index

            elif top_contour_index == 1 and middle_contour_index == 0 and bottom_contour_index == 2:
                top_contour_index = contour_area_2nd_index
                middle_contour_index = contour_area_1st_index
                bottom_contour_index = contour_area_3rd_index

            elif top_contour_index == 1 and middle_contour_index == 2 and bottom_contour_index == 0:
                top_contour_index = contour_area_2nd_index
                middle_contour_index = contour_area_3rd_index
                bottom_contour_index = contour_area_1st_index

            elif top_contour_index == 2 and middle_contour_index == 0 and bottom_contour_index == 1:
                top_contour_index = contour_area_3rd_index
                middle_contour_index = contour_area_1st_index
                bottom_contour_index = contour_area_2nd_index

            elif top_contour_index == 2 and middle_contour_index == 1 and bottom_contour_index == 0:
                top_contour_index = contour_area_3rd_index
                middle_contour_index = contour_area_2nd_index
                bottom_contour_index = contour_area_1st_index

            print('top, middle, bottom',top_contour_index,middle_contour_index,bottom_contour_index)
            top = top_contour_index
            middle = middle_contour_index
            bottom = bottom_contour_index

            #デバッグ用
            time.sleep(0.001)


            # ##### 外接短形を描く #####
            # 白い塊に接する最小の長方形を取得
            a_mid_lower = 0
            b_mid_lower = 0
            a_mid_upper = 0
            b_mid_upper = 0
            a_top_upper = 0
            b_top_upper = 0
            a_btm_upper = 0
            b_btm_upper = 0 #初期化


            rect0 = cv2.minAreaRect(contours[bottom])
            rect1 = cv2.minAreaRect(contours[middle])
            rect2 = cv2.minAreaRect(contours[top])
            # 上記長方形の4つの頂点座標を取得
            box0 = cv2.boxPoints(rect0)
            box1 = cv2.boxPoints(rect1)
            box2 = cv2.boxPoints(rect2)
            # 座標を整数にする
            box0 = np.int0(box0)
            box1 = np.int0(box1)
            box2 = np.int0(box2)

            # 長方形の傾き方向（右肩上がり、左肩上がり）によって、取得される4つの頂点座標の配列順が変わるのでif以下で統一させる
            # 左肩上がりの場合
            if box0[0, 0] >= box0[2, 0]:
                # 等高線1の配列順
                box0_1_x = box0[0, 0]
                box0_1_y = box0[0, 1]
                box0_2_x = box0[1, 0]
                box0_2_y = box0[1, 1]
                box0_3_x = box0[2, 0]
                box0_3_y = box0[2, 1]
                box0_4_x = box0[3, 0]
                box0_4_y = box0[3, 1]
            # 右肩上がりの場合
            elif box0[0, 0] < box0[2, 0]:
                # 等高線1の配列順
                box0_2_x = box0[0, 0]
                box0_2_y = box0[0, 1]
                box0_3_x = box0[1, 0]
                box0_3_y = box0[1, 1]
                box0_4_x = box0[2, 0]
                box0_4_y = box0[2, 1]
                box0_1_x = box0[3, 0]
                box0_1_y = box0[3, 1]

            # 左肩上がりの場合
            if box1[0, 0] >= box1[2, 0]:
                # 等高線2の配列順
                box1_1_x = box1[0, 0]
                box1_1_y = box1[0, 1]
                box1_2_x = box1[1, 0]
                box1_2_y = box1[1, 1]
                box1_3_x = box1[2, 0]
                box1_3_y = box1[2, 1]
                box1_4_x = box1[3, 0]
                box1_4_y = box1[3, 1]
            # 右肩上がりの場合
            elif box1[0, 0] < box1[2, 0]:
                # 等高線2の配列順
                box1_2_x = box1[0, 0]
                box1_2_y = box1[0, 1]
                box1_3_x = box1[1, 0]
                box1_3_y = box1[1, 1]
                box1_4_x = box1[2, 0]
                box1_4_y = box1[2, 1]
                box1_1_x = box1[3, 0]
                box1_1_y = box1[3, 1]

            # 左肩上がりの場合
            if box2[0, 0] >= box2[2, 0]:
                # 等高線3の配列順
                box2_1_x = box2[0, 0]
                box2_1_y = box2[0, 1]
                box2_2_x = box2[1, 0]
                box2_2_y = box2[1, 1]
                box2_3_x = box2[2, 0]
                box2_3_y = box2[2, 1]
                box2_4_x = box2[3, 0]
                box2_4_y = box2[3, 1]
            # 右肩上がりの場合
            elif box2[0, 0] < box2[2, 0]:
                # 等高線3の配列順
                box2_2_x = box2[0, 0]
                box2_2_y = box2[0, 1]
                box2_3_x = box2[1, 0]
                box2_3_y = box2[1, 1]
                box2_4_x = box2[2, 0]
                box2_4_y = box2[2, 1]
                box2_1_x = box2[3, 0]
                box2_1_y = box2[3, 1]

            # 右肩上がりの場合
            # < を <=　に変更した。=の時の処理が出来ていなくて動作が不安定だった。
            # 本来は = の時の処理も決めなければならない。= の時の配列がどうなるのか調べなければならない
            # = の時は例外も含めelseで処理したい


            print('box0_1', box0_1_x, box0_1_y)
            print('box0_2', box0_2_x, box0_2_y)
            print('box0_3', box0_3_x, box0_3_y)
            print('box0_4', box0_4_x, box0_4_y)

            print('box2_1', box2_1_x, box2_1_y)
            print('box2_2', box2_2_x, box2_2_y)
            print('box2_3', box2_3_x, box2_3_y)
            print('box2_4', box2_4_x, box2_4_y)

            position_match_3d = np.array([position_match])

            # 等高線の輪郭をカット前のフレームに表示する為、座標補正。検出枠座標（rect_pt1_3d）を足すだけ
            box0_3d = box0 + position_match_3d
            box1_3d = box1 + position_match_3d
            box2_3d = box2 + position_match_3d
            # print('box0_3d',box0_3d)

            # 上記座標を使い、等高線の輪郭をカット前のフレームに描写
            th3Cth3rect = cv2.drawContours(frame, [box0_3d], -1, (255, 0, 0), 5)
            th3Cth3rect = cv2.drawContours(frame, [box1_3d], -1, (0, 255, 0), 5)
            th3Cth3rect = cv2.drawContours(frame, [box2_3d], -1, (0, 0, 255), 5)
            # print(box0)
            # print([box0])

            # 直線式をy=ax+bとし、2点のx,y座標を代入して連立方程式でa,bを求める
            # ##### 等高線2の頂点座標から下辺の直線式を求める #####
            # 上のWaferの可変なのでContour 0 に変更　box1 -> box0

            try:
                if box1_1_y == box1_2_y:
                    box1_1_y += 0.0001
                    box1_4_y += 0.0001

                else:
                    pass

                A_mid_lower = np.array([[box1_1_x, 1.]
                                       , [box1_2_x, 1.]])
                B_mid_lower = np.array([box1_1_y, box1_2_y])
                X_mid_lower = np.linalg.solve(A_mid_lower, B_mid_lower)
                # print('X_lower=\n' + str(X_lower))
                a_mid_lower = X_mid_lower[0]
                b_mid_lower = X_mid_lower[1]
                #print('a_mid_lower(203) =', a_mid_lower)
                # a_lower: 下辺の直線式の傾き、b_lower：下辺の直線式の切片
                # print('a_lower',a_lower,'b_lower',b_lower)
                # わかりやすくするため直線式を表示しておく
                # print('y=', round(a_lower, 2), '*x+', round(b_lower, 2))
                # 20190409メモ： a_lowerが0の時は、0以外になるまで繰り返してみる？

                # ##### 次は上辺の直線式を求める #####

                A_mid_upper = np.array([[box1_3_x, 1.]
                                       , [box1_4_x, 1.]])
                B_mid_upper = np.array([box1_3_y, box1_4_y])
                X_mid_upper = np.linalg.solve(A_mid_upper, B_mid_upper)
                # print('X_upper=\n' + str(X_upper))
                a_mid_upper = X_mid_upper[0]
                b_mid_upper = X_mid_upper[1]

            except numpy.linalg.linalg.LinAlgError:
                print('numpy.linalg.linalg.LinAlgError発生したよ line 672')
                pass


            try:
                if box2_3_y == box2_4_y:
                    box2_4_y = box2_4_y + 0.0001

                else:
                    pass

                A_top_upper = np.array([[box2_3_x, 1.]
                                   , [box2_4_x, 1.]])
                B_top_upper = np.array([box2_3_y, box2_4_y])
                X_top_upper = np.linalg.solve(A_top_upper, B_top_upper)
                # print('X_lower=\n' + str(X_lower))
                a_top_upper = X_top_upper[0]
                b_top_upper = X_top_upper[1]
                #print('a_top_lower(203) =', a_top_lower)
                # a_lower: 下辺の直線式の傾き、b_lower：下辺の直線式の切片
                # print('a_lower',a_lower,'b_lower',b_lower)
                # わかりやすくするため直線式を表示しておく
                # print('y=', round(a_lower, 2), '*x+', round(b_lower, 2))
                # 20190409メモ： a_lowerが0の時は、0以外になるまで繰り返してみる？

                # ##### 次は上辺の直線式を求める #####

                if box0_3_y == box0_4_y:
                    box0_4_y = box0_4_y + 0.0001

                else:
                    pass

                A_btm_upper = np.array([[box0_3_x, 1.]
                                       , [box0_4_x, 1.]])
                B_btm_upper = np.array([box0_3_y, box0_4_y])
                X_btm_upper = np.linalg.solve(A_btm_upper, B_btm_upper)
                # print('X_upper=\n' + str(X_upper))
                a_btm_upper = X_btm_upper[0]
                b_btm_upper = X_btm_upper[1]
                # a_upper: 上辺の直線式の傾き、b_upper：上辺の直線式の切片
                # print('a_upper',a_upper,'b_upper',b_upper)
                # print('y=', round(a_upper, 2), '*x+', round(b_upper, 2))

                # 20190409メモ： a_upperが0の時は、0以外になるまで繰り返してみる？
            # エラー処理
            except numpy.linalg.linalg.LinAlgError:
                print('numpy.linalg.linalg.LinAlgError発生したよ line 707')
                pass


            # ##### 次は上辺の直線式を求める #####
            # 下のWaferの上辺なので box1 -> box 2に変更

            # 20190409追加
            # 傾きが0になると、のちの計算で分母に使っているのでエラーになるため、0の時は限りなく0として1E-8にした
            print('a_mid_lower = ',a_mid_lower)
            print('b_mid_lower = ',b_mid_lower)
            print('a_mid_upper = ',a_mid_upper)
            print('b_mid_upper = ',b_mid_upper)
            print('a_top_upper = ',a_top_upper)
            print('b_top_upper = ',b_top_upper)
            print('a_btm_upper = ',a_btm_upper)
            print('b_btm_upper = ',b_btm_upper)

            if a_mid_lower ==0 or b_mid_lower ==0 or a_mid_upper ==0 or b_mid_upper ==0 or a_top_upper ==0 or b_top_upper ==0 or a_btm_upper ==0 or b_btm_upper ==0:
                print('a or b is zero. passing')
                pass

            else:

                # ##### 上辺下辺に垂直な線の傾きa_invを求める #####
                # a_lowerの逆数で符号を逆にする
                a_mid_lower_inv = 1 / a_mid_lower * -1
                a_mid_upper_inv = 1 / a_mid_upper * -1
                a_top_upper_inv = 1 / a_top_upper * -1
                a_btm_upper_inv = 1 / a_btm_upper * -1

                # print('a_inv', a_inv)

                gap_wafers = []  # 下部Wafer上辺から上に捜索した距離

                #wafer間の距離を求める
                gap_wafer2wafer()

                print('gap_wafers',gap_wafers)


                # 引数の説明
                # x_start_position: 上側のクリアランス測定時は box1_3_x と入力。下側のクリアランス測定時は box1_2_x と入力。
                # x_offset: スタート位置を頂点からずらす量。ピクセル座標を正の整数で入力。
                # y_offset: yの走査線をシフトさせて、上下に白(255)を探しに行く。上側のクリアランス測定時は負の整数を、下側は正の整数を入力。
                # x_end_position: スタート位置と反対側の頂点のx座標。上側のクリアランス測定時は box1_4_x と入力。下側は box1_1_x と入力。
                # y_shift: 上側に捜索時は -1 と入力、下側に捜索時は 1 と入力。
                # x_shift: 次の操作位置へのシフト量で正の整数を入力
                # xy_list: 上部を上側に捜索ならgap_upper_up、上部を下側に捜索ならgap_upper_down、下部を上側に捜索ならgap_lower_up、下側を下側に捜索ならgap_lower_down
                # a(傾き),b(切片): a_mid_lower, b_mid_lower, a_mid_upper, b_mid_upper, a_top_lower, b_top_lower, a_btm_upper, b_btm_upperから選ぶ
                # a_inv: a_mid_lower_inv, a_mid_upper_inv, a_top_lower_inv, a_btm_upper_invから選ぶ

                #def gap_detector(x_start_position,x_offset_start,x_offset_end,y_offset,x_end_position,y_shift,x_shift,xy_list,a,b,a_inv)

                gap_upper_up = []  # 上辺のy_offset位置から上に捜索した距離
                gap_upper_down = []  # 上辺のy_offset位置から下に捜索した距離
                gap_lower_up = []  # 上辺のy_offset位置から上に捜索した距離
                gap_lower_down = []  # 上辺のy_offset位置から下に捜索した距離

                # 上部クリアランス、上部に捜索
                gap_detector(box1_3_x, 100, 30, -20, box1_4_x, -1, 5, gap_upper_up,a_mid_upper,b_mid_upper,a_mid_upper_inv)
                # 上部クリアランス、下部に捜索
                gap_detector(box1_3_x, 100, 30, -20, box1_4_x, 1, 5, gap_upper_down,a_mid_upper,b_mid_upper,a_mid_upper_inv)

                # 下部クリアランス、上部に捜索
                gap_detector(box1_2_x, 100, 70, 20, box1_1_x, -1, 5, gap_lower_up,a_mid_lower,b_mid_lower,a_mid_lower_inv)
                # 下部クリアランス、下部に捜索
                gap_detector(box1_2_x, 100, 70, 20, box1_1_x, 1, 5, gap_lower_down,a_mid_lower,b_mid_lower,a_mid_lower_inv)

                print('gap_upper_up',gap_upper_up)  # 上辺のy_offset位置から上に捜索した距離
                print('gap_upper_down',gap_upper_down)  # 上辺のy_offset位置から下に捜索した距離
                print('gap_lower_up',gap_lower_up)  # 上辺のy_offset位置から上に捜索した距離
                print('gap_lower_down',gap_lower_down)




                # ##### ここからは、Forkの厚みを走査型でやってみる #####
                # 上辺 y_upper = 0.03 * x_upper + 392.92
                # 下辺 y_lower = 0.03 * x_lower + 476.02
                # 垂直線 y= a_inv * x + b_inv
                # b_inv = y - a_inv * x

                # ##### 上辺から #####
                # スタートは頂点から
                x_fork_start_upper = box1_3_x + 30  # スタート地点、エッジを避けるため10ピクセル内側から始める
                y_fork_start_upper = box1_3_y  # スタート地点

                # ここで、yを頂点プラス10にする　Wafer上辺よりも10ピクセル下という意味
                y_fork_start_upper_p10 = a_mid_upper * x_fork_start_upper + b_mid_upper + 10  # n10はマイナス10の意味

                # 255までの高さをリスト化
                fork_height_up = []  # 上辺の+10から上に捜索した高さ
                fork_height_down = []  # 上辺の+10から下に捜索した高さ
                x_org = []
                y_org = []

                # スタート地点から、上辺を通ってもう一つの頂点までループ
                # print('LOOP START')
                i = 0
                re_re_th3 = cv2.imread(path + '230FLT_th3.png', 1)
                # ##### まずは上側に捜索 #####
                while x_fork_start_upper < box1_4_x - 30:  # エッジを避けるため10ピクセル内側で終わる
                    b_mid_upper_inv = y_fork_start_upper_p10 - a_mid_upper_inv * x_fork_start_upper  # 垂直線のbを求める
                    # print('b_inv', b_inv)
                    x_next = (y_fork_start_upper_p10 - b_mid_upper_inv) / a_mid_upper_inv
                    org_x_fork_start_upper = x_next
                    org_y_fork_start_upper = y_fork_start_upper_p10
                    while th3[int(y_fork_start_upper_p10), int(x_next)] >= 0:  # 垂直線をy+1ずつ移動して白いオブジェクトにあたるまでループ
                        # print(th3[int(y_wf_start_upper_p10), int(x_next)])
                        if th3[int(y_fork_start_upper_p10), int(x_next)] > 0:
                            y_fork_start_upper_p10 -= 1  # 画像上ではyは下に行くほどプラス、上に行くほどマイナス
                            x_next = (y_fork_start_upper_p10 - b_mid_upper_inv) / a_mid_upper_inv
                            # print('y_wf_start_upper_n10', y_wf_start_upper_p10)
                            # print('x_next', x_next)
                            # print('0or255:', th3[int(y_wf_start_upper_p10), int(x_next)])
                            if y_fork_start_upper_p10 < 0:
                                print('y_fork_start_upper_p10 cannot be negative value!!!')
                                break
                            elif x_next < 0:
                                print('x_next cannot be negative value!!!')
                                break
                            elif x_next > ref_pic_size[0] - 19:
                                print('x_next cannot be more than max width!!!')
                                break
                        elif th3[int(y_fork_start_upper_p10), int(x_next)] == 0:
                            y_fork_upper_0 = y_fork_start_upper_p10
                            x_fork_upper_0 = x_next
                            fork_height_up.append(np.sqrt(
                                (org_x_fork_start_upper - x_fork_upper_0) ** 2 + (org_y_fork_start_upper - y_fork_upper_0) ** 2))
                            # print('org_x_wf_start_upper', org_x_wf_start_upper)
                            # print('org_y_wf_start_upper', org_y_wf_start_upper)
                            x_org.append(int(org_x_fork_start_upper))
                            y_org.append(int(org_y_fork_start_upper))
                            # print('x_wf_upper_0', x_wf_upper_0)
                            # print('y_wf_upper_0', y_wf_upper_0)
                            # print('Wafer厚みを上側に捜索中')
                            # 捜索線を描く
                            cv2.line(frame,
                                     (int(org_x_fork_start_upper) + position_match[0], int(org_y_fork_start_upper) + position_match[1]),
                                     (int(x_fork_upper_0) + position_match[0], int(y_fork_upper_0) + position_match[1]), (0, 150, 50),
                                     thickness=3)
                            break
                        elif y_fork_start_upper < 1:
                            print('break')
                            break
                    #print('fork_height_up', fork_height_up)
                    x_fork_start_upper += 10  # 1ピクセルずつやるとかなり時間が掛かるので、20(=約1.2mm)ピクセル飛ばしでやってみる
                    #print('looping....')
                    # print('x_wf_start_upper:', x_wf_start_upper)
                    y_fork_start_upper_p10 = a_mid_upper * x_fork_start_upper + b_mid_upper + 10
                    i += 1
                    # time.sleep(1)

                # ##### 次に下側に捜索 #####
                x_fork_start_upper = box1_3_x + 30  # スタート地点、エッジを避けるため10ピクセル内側から始める
                y_fork_start_upper = box1_3_y  # スタート地点

                y_fork_start_upper_p10 = a_mid_upper * x_fork_start_upper + b_mid_upper + 10  # n10はマイナス10の意味 # 5に変更

                i = 0
                while x_fork_start_upper < box1_4_x - 30:  # エッジを避けるため100ピクセル内側で終わる
                    b_mid_upper_inv = y_fork_start_upper_p10 - a_mid_upper_inv * x_fork_start_upper  # 垂直線のbを求める
                    # print('b_inv', b_inv)
                    x_next = (y_fork_start_upper_p10 - b_mid_upper_inv) / a_mid_upper_inv
                    org_x_fork_start_upper = x_next
                    org_y_fork_start_upper = y_fork_start_upper_p10
                    while th3[int(y_fork_start_upper_p10), int(x_next)] >= 0:  # 垂直線をy+1ずつ移動して白いオブジェクトにあたるまでループ
                        # print(th3[int(y_wf_start_upper_p10), int(x_next)])
                        if th3[int(y_fork_start_upper_p10), int(x_next)] > 0:
                            y_fork_start_upper_p10 += 1  # 画像上ではyは下に行くほどプラス、上に行くほどマイナス
                            x_next = (y_fork_start_upper_p10 - b_mid_upper_inv) / a_mid_upper_inv
                            # print('y_wf_start_upper_p10', y_wf_start_upper_p10)
                            # print('x_next', x_next)
                            # print('0or255:', th3[int(y_wf_start_upper_p10), int(x_next)])
                            if y_fork_start_upper_p10 > ref_pic_size[1] - 2:
                                print('y_fork_start_upper_p10 cannot be more than max height!!!')
                                break
                            elif x_next < 0:
                                print('x_next cannot be negative value!!!')
                                break
                            elif x_next > ref_pic_size[0] - 11:
                                print('x_next cannot be more than max width!!!')
                                break
                        elif th3[int(y_fork_start_upper_p10), int(x_next)] == 0:
                            y_fork_upper_0 = y_fork_start_upper_p10
                            x_fork_upper_0 = x_next
                            fork_height_down.append(np.sqrt(
                                (org_x_fork_start_upper - x_fork_upper_0) ** 2 + (org_y_fork_start_upper - y_fork_upper_0) ** 2))
                            # print('org_x_wf_start_upper', org_x_wf_start_upper)
                            # print('org_y_wf_start_upper', org_y_wf_start_upper)
                            # print('x_wf_upper_0', x_wf_upper_0)
                            # print('y_wf_upper_0', y_wf_upper_0)
                            # print('Wafer厚みを下側に捜索中')
                            # 捜索線を描いてみる　なぜgap_upper値が徐々に小さくなるのか、、
                            cv2.line(frame,
                                     (int(org_x_fork_start_upper) + position_match[0], int(org_y_fork_start_upper) + position_match[1]),
                                     (int(x_fork_upper_0) + position_match[0], int(y_fork_upper_0) + position_match[1]), (0, 150, 50),
                                     thickness=3)
                            break
                        elif y_fork_start_upper < rect_h - 1:
                            print('break')
                            break
                    #print('fork_height_up', fork_height_down)
                    x_fork_start_upper += 10  # 1ピクセルずつやるとかなり時間が掛かるので、20(=約1.2mm)ピクセル飛ばしでやってみる
                    # print('looping....')
                    # print('x_wf_start_upper:', x_wf_start_upper)
                    y_fork_start_upper_p10 = a_mid_upper * x_fork_start_upper + b_mid_upper + 10
                    i += 1
                    # time.sleep(1)
                try:
                    # ##### Boatピッチを、検出したWafer間のピクセル数で割る　＝　mm/pixel が算出される #####
                    global gap_wafers_ave
                    if len(gap_wafers) == 0:
                        print('gap_wafers is 0!!!')
                        gap_wafers = [9999999]
                        gap_wafers_ave = sum(gap_wafers) / len(gap_wafers)
                        print('gap Average', gap_wafers_ave)
                        pixel_per_mm = gap_wafers_ave / boat_pitch # 検出厚みを実際の寸法5㎜でわる。単位はpixel/mm
                        mm_per_pixel = boat_pitch / gap_wafers_ave
                    else:
                        gap_wafers_ave = sum(gap_wafers) / len(gap_wafers)
                        print('gap Average', gap_wafers_ave)
                        pixel_per_mm = gap_wafers_ave / boat_pitch # 検出厚みを実際の寸法5㎜でわる。単位はpixel/mm
                        mm_per_pixel = boat_pitch / gap_wafers_ave # mm/pixel

                    global height_ave
                    fork_height_updown = [n1 + n2 for n1, n2 in zip(fork_height_up, fork_height_down)]
                    if len(fork_height_updown) == 0:
                        print('fork_height_updown is 0!!!')
                        fork_height_updown = [9999999]
                        height_ave = sum(fork_height_updown) / len(fork_height_updown)
                        print('Thickness Average', height_ave)
                        realrate = height_ave / fork_thickness # 検出厚みを実際の寸法5㎜でわる。単位はpixel/mm
                    else:
                        height_ave = sum(fork_height_updown) / len(fork_height_updown)
                        print('Thickness Average', height_ave)
                        realrate = height_ave / fork_thickness # 検出厚みを実際の寸法5㎜でわる。単位はpixel/mm

                    # ##### 上下のGap Pixelをmmに変換 #####
                    gap_upper_updown = [n1 + n2 for n1, n2 in zip(gap_upper_up, gap_upper_down)]
                    global real_gap_upper_ave
                    if len(gap_upper_updown) == 0:
                        print('gap_upper_updown is 0!!!')
                        gap_upper_updown = [9999999]
                        gap_upper_ave = sum(gap_upper_updown) / len(gap_upper_updown)
                        real_gap_upper_ave = gap_upper_ave * mm_per_pixel
                        print('Real Upper Gap Average mm', real_gap_upper_ave)
                    else:
                        gap_upper_ave = sum(gap_upper_updown) / len(gap_upper_updown)
                        real_gap_upper_ave = gap_upper_ave * mm_per_pixel
                        print('Real Upper Gap Average mm', real_gap_upper_ave)

                    gap_lower_updown = [n1 + n2 for n1, n2 in zip(gap_lower_up, gap_lower_down)]
                    global real_gap_lower_ave
                    if len(gap_lower_updown) == 0:
                        print('gap_lower_updown is 0!!!')
                        gap_lower_updown = [9999999]
                        gap_lower_ave = sum(gap_lower_updown) / len(gap_lower_updown)
                        real_gap_lower_ave = gap_lower_ave * mm_per_pixel
                        print('Real Lower Gap Average mm', real_gap_lower_ave)
                    else:
                        gap_lower_ave = sum(gap_lower_updown) / len(gap_lower_updown)
                        real_gap_lower_ave = gap_lower_ave * mm_per_pixel
                        print('Real Lower Gap Average mm', real_gap_lower_ave)

                    # Gap値を表示する
                    if real_gap_upper_ave < 0.001:
                        cv2.putText(frame, 'Gap Upper mm =  ----',
                                    (position_match[0], box2_3_y - 50 + position_match[1]), cv2.FONT_HERSHEY_SIMPLEX,
                                    2.0, (0, 255, 0), thickness=3)
                        cv2.putText(frame, 'Gap Lower mm =  ----',
                                    (position_match[0], box0_3_y + 100 + position_match[1]), cv2.FONT_HERSHEY_SIMPLEX,
                                    2.0, (0, 255, 0), thickness=3)

                    elif real_gap_upper_ave > 1000:
                        cv2.putText(frame, 'Gap Upper mm =  ----',
                                    (position_match[0], box2_3_y - 50 + position_match[1]), cv2.FONT_HERSHEY_SIMPLEX,
                                    2.0, (0, 255, 0), thickness=3)
                        cv2.putText(frame, 'Gap Lower mm =  ----',
                                    (position_match[0], box0_3_y + 100 + position_match[1]), cv2.FONT_HERSHEY_SIMPLEX,
                                    2.0, (0, 255, 0), thickness=3)

                    else:
                        cv2.putText(frame, 'Gap Upper mm =' + str(round(real_gap_upper_ave, 2)),
                                    (position_match[0], box2_3_y - 50 + position_match[1]), cv2.FONT_HERSHEY_SIMPLEX, 2.0,
                                    (0, 255, 0), thickness=3)
                        cv2.putText(frame, 'Gap Lower mm =' + str(round(real_gap_lower_ave, 2)),
                                    (position_match[0], box0_3_y + 100 + position_match[1]), cv2.FONT_HERSHEY_SIMPLEX, 2.0,
                                    (0, 255, 0), thickness=3)

                except ZeroDivisionError:
                    print('len(gap_wafers)',len(gap_wafers))
                    print('len(gap_upper_updown)',len(gap_upper_updown))
                    print('mm_per_pixel',mm_per_pixel)
                    print('len(gap_lower_updown)',len(gap_lower_updown))
                    pass

                # ############上記までで、距離とWafer厚みの値を取得した

                # ここからは、表示値を安定させるための工夫
                # 毎回X回分の平均値を計算
                gap_upper_xave.append(round(real_gap_upper_ave, 3))
                gap_lower_xave.append(round(real_gap_lower_ave, 3))

                if len(gap_lower_xave) == ave_len:
                    gap_upper_xave_ave = sum(gap_upper_xave) / len(gap_upper_xave)
                    gap_lower_xave_ave = sum(gap_lower_xave) / len(gap_lower_xave)
                    gap_upper_xave_ave_list.append(gap_upper_xave_ave)
                    gap_lower_xave_ave_list.append(gap_lower_xave_ave)
                    gap_upper_xave_ave_list.pop(0)
                    gap_lower_xave_ave_list.pop(0)
                    print('gap_upper_xave_ave_list',gap_upper_xave_ave_list)
                    print('gap_lower_xave_ave_list',gap_lower_xave_ave_list)
                    del gap_upper_xave[:]
                    del gap_lower_xave[:]

                # 平均値を表示する
                cv2.putText(frame, 'Gap Upper ' + str(ave_len) + 'X Ave mm =' + str(round(gap_upper_xave_ave_list[0], 2)),(- 150 + rect_pt1[0], rect_pt1[1] - 120), cv2.FONT_HERSHEY_SIMPLEX, 2.0,(0, 0, 255), thickness=3)
                cv2.putText(frame, 'Gap Lower ' + str(ave_len) + 'X Ave mm =' + str(round(gap_lower_xave_ave_list[0], 2)),(- 150 + rect_pt1[0], rect_pt1[1] + 630), cv2.FONT_HERSHEY_SIMPLEX, 2.0,(0, 0, 255), thickness=3)

                #cv2.imshow('th3', th3)
                # cv2.imshow('th3Cth3', th3Cth3)
                #cv2.imshow('th3Cth3rect', th3Cth3rect)

                ### Gapピクセル値の合計(Upper, Lower, Wafer thickness) rev4c追加分
                Totalgap = gap_upper_ave + gap_lower_ave + height_ave
                print('Totalgap', Totalgap)
                pixpermm = Totalgap / 19.225
                print('pixpermm: ',pixpermm)
                print('0.775*pixpermm :',0.775*pixpermm)
                print('height_ave: ',height_ave)

                cv2.putText(frame, 'boat_pitch (mm)' + str(boat_pitch),
                            (- 150 + rect_pt1[0], rect_pt1[1] + 830), cv2.FONT_HERSHEY_SIMPLEX, 2.0,
                            (0, 0, 255), thickness=3)
                cv2.putText(frame, 'detected fork thickness (mm)' + str(round(height_ave*mm_per_pixel, 1)),
                            (- 150 + rect_pt1[0], rect_pt1[1] + 730), cv2.FONT_HERSHEY_SIMPLEX, 2.0,
                            (0, 0, 255), thickness=3)
                # 両者の値が同じになるようにハード調整する必要がある。上記値追加はまずはその目安として使用する。

                #cv2.imshow('th3', th3)
                # resized_frame_cutと同じサイズで2値化後の映像を表示
                resized_th3 = cv2.resize(th3, (int((rect_pt2[0]-rect_pt1[0]) / 3), int((rect_pt2[1]-rect_pt1[1]) / 3)))
                #cv2.imshow('resized_th3', resized_th3)
                # cv2.imshow('th3Cth3', th3Cth3)
                #cv2.imshow('th3Cth3rect', th3Cth3rect)
                resized_th3Cth3rect = cv2.resize(th3Cth3rect, (int(frame_width/2), int(frame_height/2)))
                cv2.imshow('resized_th3Cth3rect', resized_th3Cth3rect)
                cv2.moveWindow('resized_th3Cth3rect', 0, 0)
                cv2.moveWindow('resized_frame_cut', 1000, 0)
                cv2.moveWindow('resized_th3', 1000, 300)
        else:
            pass

    else:
        pass
    # print('passing...')
    k = cv2.waitKey(1)
    if k == 27:
        break
    # print('looping.......')
    time.sleep(0.001)

cap.release()
cv2.destroyAllWindows()
