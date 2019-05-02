from src.auxiliaries import create_test_img
from skimage.feature import blob_dog, blob_log, blob_doh
import cv2
from math import sqrt
from scipy.spatial import KDTree
import timeit
import numpy as np


def get_accuracy(kd_tree, blob_list, center_list, threshold):
    """
    Calculate true positives, false positives,

    :param kd_tree: scipy.spatial.KDTree of real centers
    :param blob_list: list of predicted centers
    :param center_list: list of real centers
    :param threshold: max accepted distance between prediction and real center to count as correct
    :return: [true_positive_rate, false_positive_rate, detected_centers_rate]
    """
    num_real_centers = len(center_list)
    num_pred_centers = len(blob_list)
    correct_pred = 0
    false_pred = 0

    for blob in blob_list:
        dist, idx = kd_tree.query(blob[0:2])

        if dist < threshold:
            correct_pred += 1
        else:
            false_pred += 1
    if num_pred_centers != 0:
        return [
            correct_pred / num_pred_centers,
            false_pred / num_pred_centers,
            correct_pred / num_real_centers,
        ]
    else:
        return [0, 1, 0]


def compare_blob_detection(num_runs=4, threshold=3):
    """
    Compare speed and detection rate of different standard tools

    :param num_runs: Number of test runs to be averaged
    :param threshold: max accepted distance between prediction and real center to count as correct
    """
    log_time = 0
    dog_time = 0
    doh_time = 0
    sbd_time = 0

    log_acc = []
    dog_acc = []
    doh_acc = []
    sbd_acc = []

    for ii in range(num_runs):
        image, center_list, radius_list = create_test_img(
            size=(75, 75), num_points=50, radius_min=3, radius_max=10, random_seed=ii
        )
        # Build KD Tree for later evaluation
        center_kd_tree = KDTree(center_list)

        # Laplacian of Gaussian
        start_log = timeit.default_timer()
        blobs_log = blob_log(image, min_sigma=1, max_sigma=3, num_sigma=3, overlap=1)
        stop_log = timeit.default_timer()
        log_time += stop_log - start_log
        blobs_log[:, 2] = blobs_log[:, 2] * sqrt(2)
        log_acc.append(get_accuracy(center_kd_tree, blobs_log, center_list, threshold))

        # Difference of Gaussian
        start_dog = timeit.default_timer()
        blobs_dog = blob_dog(image, min_sigma=1, max_sigma=3, overlap=1)
        stop_dog = timeit.default_timer()
        dog_time += stop_dog - start_dog
        blobs_dog[:, 2] = blobs_dog[:, 2] * sqrt(2)
        dog_acc.append(get_accuracy(center_kd_tree, blobs_dog, center_list, threshold))

        # Difference of Hessian
        start_doh = timeit.default_timer()
        blobs_doh = blob_doh(image, min_sigma=1, max_sigma=3, overlap=1)
        stop_doh = timeit.default_timer()
        doh_time += stop_doh - start_doh
        doh_acc.append(get_accuracy(center_kd_tree, blobs_doh, center_list, threshold))

        # Simple Blob Detector opencv
        is_v2 = cv2.__version__.startswith("2.")
        if is_v2:
            detector = cv2.SimpleBlobDetector()
        else:
            detector = cv2.SimpleBlobDetector_create()

        params = cv2.SimpleBlobDetector_Params()
        params.blobColor = 255

        image_8bit = image.astype("uint8")

        start_sbd = timeit.default_timer()
        keypoints = detector.detect(image_8bit)
        stop_sbd = timeit.default_timer()
        sbd_time += stop_sbd - start_sbd
        sbd_acc.append(get_accuracy(center_kd_tree, keypoints, center_list, threshold))

    # Average Time over runs
    log_time = log_time / num_runs
    dog_time = dog_time / num_runs
    doh_time = doh_time / num_runs
    sbd_time = sbd_time / num_runs

    # Convert arrays to numpy
    log_acc = np.array(log_acc)
    dog_acc = np.array(dog_acc)
    doh_acc = np.array(doh_acc)
    sbd_acc = np.array(sbd_acc)

    # Average Results over runs
    print("Average results: ")
    print(
        "Laplacian of Gaussian:  \t %2.5f s, TP: %2.2f,\t DC: %2.2f"
        % (log_time, np.mean(log_acc[:, 0]), np.mean(log_acc[:, 2]))
    )

    print(
        "Difference of Gaussian: \t %2.5f s, TP: %2.2f,\t DC: %2.2f"
        % (dog_time, np.mean(dog_acc[:, 0]), np.mean(dog_acc[:, 2]))
    )

    print(
        "Difference of Hessian:  \t %2.5f s, TP: %2.2f,\t DC: %2.2f"
        % (doh_time, np.mean(doh_acc[:, 0]), np.mean(doh_acc[:, 2]))
    )

    print(
        "Simple Blob Detector:   \t %2.5f s, TP: %2.2f,\t DC: %2.2f"
        % (sbd_time, np.mean(sbd_acc[:, 0]), np.mean(sbd_acc[:, 2]))
    )


if __name__ == "__main__":
    compare_blob_detection()
