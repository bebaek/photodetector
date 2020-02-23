import cv2
import matplotlib.pyplot as plt
import numpy as np
from numpy.linalg import norm


def main():
    im = cv2.imread('data/3ladies1.jpg')
    imgray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

    # Make a binary image
    ret, thresh = cv2.threshold(imgray, 240, 255, cv2.THRESH_BINARY_INV)

    # Remove noise
    kernel = np.ones((5, 5), np.uint8)
    closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # Find contours
    all_contours, hierarchy = cv2.findContours(
        closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = []
    for cnt in all_contours:
        if cv2.contourArea(cnt) > 400:
            contours.append(cnt)

    # Draw contours
    boxes = []
    for cnt in contours:
        rect = cv2.minAreaRect(cnt)
        box = cv2.boxPoints(rect)
        boxes.append(np.int0(box))
    im_cnt = np.copy(im)
    cv2.drawContours(im_cnt, boxes, -1, (0, 255, 0), 2)
    im_cnt = cv2.cvtColor(im_cnt, cv2.COLOR_BGR2RGB)

    # Crop inside contours
    cropped = []
    for i, box in enumerate(boxes):
        # Get all the points inside the box
        mask = np.zeros(im.shape, np.uint8)
        cv2.drawContours(mask, [box], 0, (255, 255, 255), -1)
        masked = np.bitwise_and(mask, im)

        # Crop
        xmin = np.amin(box[:, 0])
        xmax = np.amax(box[:, 0])
        ymin = np.amin(box[:, 1])
        ymax = np.amax(box[:, 1])
        cropped = masked[ymin:ymax + 1, xmin:xmax + 1]

        # Correct tilt
        vtop = box[np.argmin(box[:, 1])]
        vleft = box[np.argmin(box[:, 0])]
        vright = box[np.argmax(box[:, 0])]
        angle = np.arctan((vright[1] - vtop[1]) / (vright[0] - vtop[0])) \
            * 180 / np.pi
        if angle > 45:
            angle = -(90 - angle)
        center = ((xmax - xmin)/2, (ymax - ymin)/2)
        mat = cv2.getRotationMatrix2D(center, angle, 1)
        cropped_size = cropped.shape[1::-1]
        untilted = cv2.warpAffine(cropped, mat, cropped_size)

        # Final crop
        size = (int(norm(vright - vtop)), int(norm(vleft - vtop)))
        if angle < 0:
            size = size[::-1]
        xmin = int(cropped_size[0] / 2 - size[0] / 2) + 1  # Clip border px 1
        xmax = int(cropped_size[0] / 2 + size[0] / 2) - 1
        ymin = int(cropped_size[1] / 2 - size[1] / 2) + 1
        ymax = int(cropped_size[1] / 2 + size[1] / 2) - 1
        subim = untilted[ymin:ymax + 1, xmin:xmax + 1]

        # Show
        plt.subplot(121)
        plt.imshow(im_cnt)
        plt.subplot(122)
        subim_rgb = cv2.cvtColor(subim, cv2.COLOR_BGR2RGB)
        plt.imshow(subim_rgb)
        plt.show()

        # Save
        cv2.imwrite(f'img{i}.jpg', subim)


if __name__ == '__main__':
    main()
