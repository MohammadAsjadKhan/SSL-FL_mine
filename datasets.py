# --------------------------------------------------------
# Based on BEiT and MAE code bases
# https://github.com/microsoft/unilm/tree/master/beit
# https://github.com/facebookresearch/mae
# Author: Rui Yan
# --------------------------------------------------------

import os
import torch

from torchvision import datasets, transforms

from timm.data.constants import \
    IMAGENET_DEFAULT_MEAN, IMAGENET_DEFAULT_STD, IMAGENET_INCEPTION_MEAN, IMAGENET_INCEPTION_STD
from transforms import RandomResizedCropAndInterpolationWithTwoPic
from timm.data import create_transform

from dall_e.utils import map_pixels
from masking_generator import MaskingGenerator

from PIL import Image
from skimage.transform import resize

Image.LOAD_TRUNCATED_IMAGES = True

CIFAR10_DEFAULT_MEAN = (0.49139968, 0.48215841, 0.44653091)
CIFAR10_DEFAULT_STD = (0.24703223, 0.24348513, 0.26158784)

RETINA_MEAN = (0.5007, 0.5010, 0.5019)
RETINA_STD = (0.0342, 0.0535, 0.0484)

# DEFAULT_MEAN = (0.485, 0.456, 0.406)
# DEFAULT_STD = (0.229, 0.224, 0.225)

# ISIC_MEAN = (0.49139968, 0.48215827, 0.44653124)
# ISIC_STD = (0.24703233, 0.24348505, 0.26158768)

class DataAugmentationForPretrain(object):
    def __init__(self, args):
        
        if args.data_set == 'CIFAR10':
            mean = CIFAR10_DEFAULT_MEAN
            std = CIFAR10_DEFAULT_MEAN
        elif args.data_set == 'IMNET':
            imagenet_default_mean_and_std = args.imagenet_default_mean_and_std
            mean = IMAGENET_INCEPTION_MEAN if not imagenet_default_mean_and_std else IMAGENET_DEFAULT_MEAN
            std = IMAGENET_INCEPTION_STD if not imagenet_default_mean_and_std else IMAGENET_DEFAULT_STD
        elif args.data_set == 'Retina':
            mean, std = RETINA_MEAN, RETINA_STD
        else:
            mean, std = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)
        
        if args.model_name == 'beit':
            if args.aug == 'aug_1':
                self.common_transform = transforms.Compose([
                    transforms.ColorJitter(0.4, 0.4, 0.4),
                    transforms.RandomHorizontalFlip(p=0.5),
                    RandomResizedCropAndInterpolationWithTwoPic(
                        size=args.input_size, second_size=args.second_input_size,
                        interpolation=args.train_interpolation,
                        second_interpolation=args.second_interpolation,
                    ),
                ])
            elif args.aug == 'aug_2':
                if args.data_set == 'Retina':
                    '''https://github.com/xmengli/self_supervised/blob/master/main.py'''
                    self.common_transform = transforms.Compose([
                        transforms.RandomGrayscale(p=0.2),
                        transforms.ColorJitter(0.4, 0.4, 0.4),
                        transforms.RandomHorizontalFlip(p=0.5),
                        RandomResizedCropAndInterpolationWithTwoPic(
                            size=args.input_size, second_size=args.second_input_size,
                            scale=(0.2, 1.0),
                            interpolation=args.train_interpolation,
                            second_interpolation=args.second_interpolation,
                        ),
                    ])
                elif args.data_set == 'COVIDfl':
                    self.common_transform = transforms.Compose([
                        transforms.ColorJitter(hue=.05, saturation=.05),
                        transforms.RandomHorizontalFlip(p=0.5),
                        RandomResizedCropAndInterpolationWithTwoPic(
                            size=args.input_size, second_size=args.second_input_size,
                            scale=(0.4, 1.0),
                            interpolation=args.train_interpolation,
                            second_interpolation=args.second_interpolation,
                        ),
                    ])
                elif args.data_set == 'ISIC':
                    self.common_transform = transforms.Compose([
                        transforms.ColorJitter(0.4, 0.4, 0.4),
                        transforms.RandomHorizontalFlip(p=0.5),
                        RandomResizedCropAndInterpolationWithTwoPic(
                            size=args.input_size, second_size=args.second_input_size,
                            scale=(0.2, 1.0),
                            interpolation=args.train_interpolation,
                            second_interpolation=args.second_interpolation,
                        ),
                    ])
                    
            elif args.aug == 'aug_3':
                if args.data_set == 'ISIC':
                    self.common_transform = transforms.Compose([
                        transforms.ColorJitter(0.3, 0.3, 0.3, 0.1),
                        transforms.RandomHorizontalFlip(p=0.5),
                        RandomResizedCropAndInterpolationWithTwoPic(
                            size=args.input_size, second_size=args.second_input_size,
                            scale=(0.6, 1.2),
                            interpolation=args.train_interpolation,
                            second_interpolation=args.second_interpolation,
                        ),
                    ])
                else:
                    print(f'{args.data_set} does not have {args.aug}')
            
            # visual_token_transform
            if args.discrete_vae_type == "dall-e":
                self.visual_token_transform = transforms.Compose([
                    transforms.ToTensor(),
                    map_pixels,
                ])
            elif args.discrete_vae_type == "customized":
                self.visual_token_transform = transforms.Compose([
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=torch.tensor(mean),
                        std=torch.tensor(std),
                    ),
                ])
            else:
                raise NotImplementedError()
                
            self.masked_position_generator = MaskingGenerator(
                args.window_size, num_masking_patches=args.num_mask_patches,
                max_num_patches=args.max_mask_patches_per_block,
                min_num_patches=args.min_mask_patches_per_block,
            )
        
        elif args.model_name == 'mae':
            if args.aug == 'aug_1':
                self.common_transform = transforms.Compose([
                    transforms.RandomResizedCrop(args.input_size, scale=(0.2, 1.0), interpolation=3),  # 3 is bicubic
                    transforms.RandomHorizontalFlip(p=0.5)])
            
            elif args.aug == 'aug_2':
                if args.data_set == 'Retina':
                    self.common_transform = transforms.Compose([
                        transforms.RandomResizedCrop(args.input_size, scale=(0.2, 1.0), interpolation=3),  # 3 is bicubic   
                        transforms.RandomGrayscale(p=0.2),
                        transforms.ColorJitter(0.4, 0.4, 0.4),
                        transforms.RandomHorizontalFlip(p=0.5)])
                    
                elif args.data_set == 'COVIDfl':
                    self.common_transform = transforms.Compose([
                        transforms.RandomResizedCrop(args.input_size, scale=(0.4, 1.0), interpolation=3),  # 3 is bicubic
                        transforms.ColorJitter(hue=.05, saturation=.05),
                        transforms.RandomHorizontalFlip(p=0.5)])
            
                elif args.data_set == 'ISIC':
                    self.common_transform = transforms.Compose([
                        transforms.RandomResizedCrop(args.input_size, scale=(0.2, 1.0), interpolation=3),  # 3 is bicubic
                        transforms.RandomGrayscale(p=0.2),
                        transforms.ColorJitter(0.1, 0.1, 0.1),
                        transforms.RandomHorizontalFlip(p=0.5)])
            
            elif args.aug == 'aug_3':
                if args.data_set == 'ISIC':
                    self.common_transform = transforms.Compose([
                        transforms.RandomResizedCrop(args.input_size, scale=(0.6, 1.2), interpolation=3),  # 3 is bicubic
                        transforms.ColorJitter(0.3, 0.3, 0.3, 0.1),
                        transforms.RandomHorizontalFlip(p=0.5)])
                else:
                    print(f'{args.data_set} does not have {args.aug}')
        
        self.patch_transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(
                mean=torch.tensor(mean),
                std=torch.tensor(std))
        ])
        
        self.args = args
    
    def __call__(self, image):
        if self.args.model_name == 'beit':
            for_patches, for_visual_tokens = self.common_transform(image)
            return \
                self.patch_transform(for_patches), self.visual_token_transform(for_visual_tokens), \
                self.masked_position_generator()
        elif self.args.model_name == 'mae':
            for_patches = self.common_transform(image)
            return self.patch_transform(for_patches)
    
    def __repr__(self):
        if self.args.model_name == 'beit':
            repr = "(DataAugmentationForBEiT,\n"
            repr += "  common_transform = %s,\n" % str(self.common_transform)
            repr += "  patch_transform = %s,\n" % str(self.patch_transform)
            repr += "  visual_tokens_transform = %s,\n" % str(self.visual_token_transform)
            repr += "  Masked position generator = %s,\n" % str(self.masked_position_generator)
            repr += ")"
            
        elif self.args.model_name == 'mae':
            repr = "(DataAugmentationFoMAE,\n"
            repr += "  common_transform = %s,\n" % str(self.common_transform)
            repr += "  patch_transform = %s,\n" % str(self.patch_transform)
        
        return repr

def build_transform(is_train, mode, args):
    resize_im = args.input_size > 32
    
    if args.data_set == 'CIFAR10':
        mean = CIFAR10_DEFAULT_MEAN
        std = CIFAR10_DEFAULT_MEAN
    elif args.data_set == 'IMNET':
        imagenet_default_mean_and_std = args.imagenet_default_mean_and_std
        mean = IMAGENET_INCEPTION_MEAN if not imagenet_default_mean_and_std else IMAGENET_DEFAULT_MEAN
        std = IMAGENET_INCEPTION_STD if not imagenet_default_mean_and_std else IMAGENET_DEFAULT_STD
    elif args.data_set == 'Retina':
        mean, std = RETINA_MEAN, RETINA_STD
    elif args.data_set == 'Retina':
        mean, std = RETINA_MEAN, RETINA_STD
    else:
        mean, std = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)
        
    if mode == 'finetune':
        if args.data_set == 'CIFAR10':
            if is_train:
                # this should always dispatch to transforms_imagenet_train
                transform = create_transform(
                    input_size=args.input_size,
                    is_training=True,
                    color_jitter=args.color_jitter,
                    auto_augment=args.aa,
                    interpolation=args.train_interpolation,
                    re_prob=args.reprob,
                    re_mode=args.remode,
                    re_count=args.recount,
                    mean=mean,
                    std=std,
                )
                if not resize_im:
                    # replace RandomResizedCropAndInterpolation with
                    # RandomCrop
                    transform.transforms[0] = transforms.RandomCrop(
                        args.input_size, padding=4)

            else:
                t = []
                size = int((256 / 224) * 224)
                t.append(
                    transforms.Resize(size, interpolation=3),  # to maintain same ratio w.r.t. 224 images
                )
                t.append(transforms.CenterCrop(args.input_size))
                t.append(transforms.ToTensor())
                t.append(transforms.Normalize(mean, std))
                transform = transforms.Compose(t)
            
        else:
            if is_train:
                if args.data_set == 'Retina':
                    transform = transforms.Compose([
                        transforms.RandomResizedCrop(args.input_size, scale=(0.6, 1.)),
                        transforms.RandomRotation(degrees=10),
                        transforms.RandomHorizontalFlip(),
                        transforms.ToTensor(), 
                        transforms.Normalize(
                            mean=torch.tensor(mean),
                            std=torch.tensor(std))
                        ])
                elif args.data_set == 'COVIDfl':
                    transform = transforms.Compose([
                        transforms.RandomResizedCrop(args.input_size, scale=(0.8, 1.2)),
                        transforms.RandomRotation(degrees=10),
                        transforms.RandomHorizontalFlip(),
                        transforms.ToTensor(), 
                        transforms.Normalize(
                            mean=torch.tensor(mean),
                            std=torch.tensor(std))
                        ])
                elif args.data_set == 'ISIC':
                    transform = transforms.Compose([
                        transforms.RandomResizedCrop(args.input_size, scale=(0.6, 1.)),
                        transforms.RandomRotation(degrees=10),
                        transforms.RandomHorizontalFlip(),
                        transforms.ToTensor(),
                        transforms.Normalize(
                            mean=torch.tensor(mean),
                            std=torch.tensor(std))
                        ])
                        
            else:
                transform = transforms.Compose([
                    transforms.Resize([args.input_size, args.input_size]),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=torch.tensor(mean),
                        std=torch.tensor(std))
                    ])
    elif mode == 'linprob':
        if is_train:
            transform = transforms.Compose([
                RandomResizedCrop(224, interpolation=3),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])
        else:
            transform = transforms.Compose([
                transforms.Resize(256, interpolation=3),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])

    return transform
