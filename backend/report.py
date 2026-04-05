from calculateDefect import detect_defects
from localizeDefect import detect_and_localize_defects
from locate_sem import locate_sem_defect
from sem_inference import predict
import os
import numpy as np
from visualTransformer import find_defects


def change_file_path(input_path):
    directory, file_name = os.path.split(input_path)
    new_directory = directory.replace('png_files', 'npy_files')
    new_file_name = os.path.splitext(file_name)[0] + '.npy'
    new_path = os.path.join(new_directory, new_file_name)
    return new_path

def generate_report(image_path):
    if "sem" in image_path:
        localization,loc_image = locate_sem_defect(image_path)
        result = {
            'classification': predict(image_path),
            'defect_percentage': {
                'value': "The defect percentage cannot be calculated for SEM images.",
                'image_path': ""
            },
            'localization': {
                'value': localization,
                'image_path': loc_image
            }
        }
        return result
    else:
        defect_percentage, per_image = detect_defects(npy_path=change_file_path(image_path))
        localization, loc_image = detect_and_localize_defects(npy_path=change_file_path(image_path))
        image_path = change_file_path(image_path)
        array = np.load(image_path, allow_pickle=True)
        array = np.expand_dims(array, -1)  # Add batch dimension
        image = np.array([array])
        output = find_defects(image)
        result ={
                'classification': output,
                'defect_percentage': {
                    'value': defect_percentage,
                    'image_path': per_image
                },
                'localization': {
                    'value': localization,
                    'image_path': loc_image
                }
                }
        return result


