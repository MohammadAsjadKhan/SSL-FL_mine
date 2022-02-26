#!/bin/bash

cd /home/yan/SSL-FL/unilm/beit/

DATASET='Retina'
SPLIT_TYPE='split_1'
N_CLASSES=2
DATA_PATH="/data/yan/SSL-FL/${DATASET}/"
N_CLIENTS=5

# ------------------ pretrain ----------------- #
# EPOCHS=1000
# # EPOCHS=2000
# # LR='5e-4'
# LR='1.5e-3'
# BATCH_SIZE=64
# OUTPUT_PATH="/data/yan/SSL-FL/fedavg_model_ckpt_${N_CLIENTS}/${DATASET}_pretrained_beit_base/pretrained_epoch${EPOCHS}_${SPLIT_TYPE}_lr${LR}_bs${BATCH_SIZE}"

# CUDA_VISIBLE_DEVICES=0 python run_beit_pretraining_FedAvg.py \
#         --data_path ${DATA_PATH} \
#         --data_set ${DATASET} \
#         --output_dir ${OUTPUT_PATH} \
#         --lr ${LR} \
#         --batch_size ${BATCH_SIZE} \
#         --save_ckpt_freq 20 \
#         --max_communication_rounds ${EPOCHS} \
#         --split_type ${SPLIT_TYPE} \
#         --num_mask_patches 75 \
#         --model beit_base_patch16_224_8k_vocab \
#         --discrete_vae_weight_path /data/yan/SSL-FL/tokenizer_weight \
#         --warmup_epochs 10 \
#         --clip_grad 3.0 --drop_path 0.1 --layer_scale_init_value 0.1 \
#         --n_clients ${N_CLIENTS} --E_epoch 1  --num_local_clients -1 \

EPOCHS=800
# EPOCHS=2000
# LR='5e-4'
LR='2e-3'
MIN_LR='1e-5'
# BATCH_SIZE=16
# LR='3e-3'
BATCH_SIZE=64

OUTPUT_PATH="/data/yan/SSL-FL/fedavg_model_ckpt_${N_CLIENTS}/${DATASET}_pretrained_beit_base/pretrained_epoch${EPOCHS}_${SPLIT_TYPE}_lr${LR}_min_lr${MIN_LR}_bs${BATCH_SIZE}_dis"

# CUDA_VISIBLE_DEVICES=0,1,2,3 OMP_NUM_THREADS=1 python -m torch.distributed.launch --nproc_per_node=4 run_beit_pretraining_FedAvg_distributed.py \
#         --data_path ${DATA_PATH} \
#         --data_set ${DATASET} \
#         --output_dir ${OUTPUT_PATH} \
#         --lr ${LR} \
#         --min_lr ${MIN_LR} \
#         --batch_size ${BATCH_SIZE} \
#         --save_ckpt_freq 50 \
#         --max_communication_rounds ${EPOCHS} \
#         --split_type ${SPLIT_TYPE} \
#         --num_mask_patches 75 \
#         --model beit_base_patch16_224_8k_vocab \
#         --discrete_vae_weight_path /data/yan/SSL-FL/tokenizer_weight \
#         --warmup_epochs 10 --sync_bn \
#         --clip_grad 3.0 --drop_path 0.1 --layer_scale_init_value 0.1 \
#         --n_clients ${N_CLIENTS} --E_epoch 1  --num_local_clients -1 \

# ------------------ finetune ----------------- #
# CKPT_PATH="${OUTPUT_PATH}/checkpoint-1999.pth"
# CKPT_PATH="${OUTPUT_PATH}/checkpoint-999.pth"
# # LR='5e-4'
# # LR='1.5e-3'
# FT_EPOCHS=100
# OUTPUT_PATH_FT="/data/yan/SSL-FL/fedavg_model_ckpt_${N_CLIENTS}/${DATASET}_pretrained_beit_base/pretrained_epoch${EPOCHS}_lr${LR}_bs${BATCH_SIZE}/finetune_${DATASET}_epoch${FT_EPOCHS}_${SPLIT_TYPE}_lr${LR}_bs${BATCH_SIZE}"

# CUDA_VISIBLE_DEVICES=0 python run_class_finetuning_FedAvg.py \
#      --data_path ${DATA_PATH} \
#      --data_set ${DATASET} \
#      --finetune ${CKPT_PATH} \
#      --nb_classes ${N_CLASSES} \
#      --output_dir ${OUTPUT_PATH_FT} \
#      --lr ${LR} \
#      --save_ckpt_freq 50 \
#      --model beit_base_patch16_224 \
#      --batch_size ${BATCH_SIZE} --update_freq 1 --split_type ${SPLIT_TYPE} \
#      --warmup_epochs 5 --layer_decay 0.65 --drop_path 0.2 \
#      --weight_decay 0.05 --layer_scale_init_value 0.1 --clip_grad 3.0 \
#      --n_clients ${N_CLIENTS} --E_epoch 1 --max_communication_rounds ${FT_EPOCHS} --num_local_clients -1 
        
CKPT_PATH="${OUTPUT_PATH}/checkpoint-799.pth"
FT_EPOCHS=100
FT_LR='3e-3'
FT_BATCH_SIZE=32
OUTPUT_PATH_FT="/data/yan/SSL-FL/fedavg_model_ckpt_${N_CLIENTS}/${DATASET}_pretrained_beit_base/pretrained_epoch${EPOCHS}_lr${LR}_bs${BATCH_SIZE}_dis/finetune_${DATASET}_epoch${FT_EPOCHS}_${SPLIT_TYPE}_lr${FT_LR}_bs${FT_BATCH_SIZE}"

CUDA_VISIBLE_DEVICES=0,1,2,3 OMP_NUM_THREADS=1 python -m torch.distributed.launch --nproc_per_node=4 run_class_finetuning_FedAvg_distributed.py \
     --data_path ${DATA_PATH} \
     --data_set ${DATASET} \
     --finetune ${CKPT_PATH} \
     --nb_classes ${N_CLASSES} \
     --output_dir ${OUTPUT_PATH_FT} \
     --lr ${LR} \
     --save_ckpt_freq 50 \
     --model beit_base_patch16_224 \
     --batch_size ${BATCH_SIZE} --update_freq 1 --split_type ${SPLIT_TYPE} \
     --warmup_epochs 5 --layer_decay 0.65 --drop_path 0.2 \
     --weight_decay 0.05 --layer_scale_init_value 0.1 --clip_grad 3.0 \
     --n_clients ${N_CLIENTS} --E_epoch 1 --max_communication_rounds ${FT_EPOCHS} --num_local_clients -1 

# # ------------------ evaluate ----------------- #
# CKPT_PATH="${OUTPUT_PATH_FT}/checkpoint-best.pth"
# CUDA_VISIBLE_DEVICES=0 python run_class_finetuning_FedAvg_distributed.py \
#     --eval --model beit_base_patch16_224 --data_path $DATA_PATH \
#     --nb_classes ${N_CLASSES} --data_set ${DATASET} \
#     --resume $CKPT_PATH \
#     --batch_size ${BATCH_SIZE} \
#     --E_epoch 1 --max_communication_rounds 100 --num_local_clients -1 --split_type ${SPLIT_TYPE}
