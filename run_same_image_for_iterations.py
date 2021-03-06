#!/usr/bin/env python
'''
ROI Constraint UNIT
Bicheng Luo (UNI:bl2679)
A script to generate image translation results for multiple generators
'''
from datasets import *
import os
import sys
from trainers import *
import cv2
import torchvision
from tools import *
import glob
from optparse import OptionParser
parser = OptionParser()
parser.add_option('--prefix', type=str, help='prefix for .PKLs files')
parser.add_option('--output', type=str, help='output folder')
parser.add_option('--a2b',type=int,help="1 for a2b and others for b2a",default=1)
parser.add_option('--config',type=str,help="net configuration")
parser.add_option('--image_name',type=str)

#bl2679
def main(argv):
  (opts, args) = parser.parse_args(argv)

  # Load experiment setting
  assert isinstance(opts, object)
  config = NetConfig(opts.config)

  ######################################################################################################################
  # Read training parameters from the yaml file
  hyperparameters = {}
  for key in config.hyperparameters:
    exec ('hyperparameters[\'%s\'] = config.hyperparameters[\'%s\']' % (key,key))
  if opts.a2b==1:
    dataset = config.datasets['train_a']
  else:
    dataset = config.datasets['train_b']
  data = []
  exec ("data = %s(dataset)" % dataset['class_name'])
  exec("trainer=%s(config.hyperparameters)" % config.hyperparameters['trainer'])

  directory = os.path.dirname(opts.output)
  if not os.path.exists(directory):
      os.makedirs(directory)
  weight_files = glob.glob(opts.prefix + '_gen*.pkl')
  for weight_path in weight_files:
    # Prepare network
    trainer.gen.load_state_dict(torch.load(weight_path))
    trainer.cuda(0)
    trainer.gen.eval()

    full_img_name = opts.image_name
    img = data._load_one_image(full_img_name,test=True)
    raw_data = img.transpose((2, 0, 1))  # convert to HWC
    final_data = torch.FloatTensor((raw_data / 255.0 - 0.5) * 2)
    final_data = final_data.contiguous()
    final_data = Variable(final_data.view(1,final_data.size(0),final_data.size(1),final_data.size(2))).cuda(0)
    # trainer.gen.eval()
    if opts.a2b == 1:
      output_data = trainer.gen.forward_a2b(final_data)
    else:
      output_data = trainer.gen.forward_b2a(final_data)
    basename = os.path.basename(os.path.splitext(weight_path)[0])
    assembled_images = torch.cat((final_data, output_data[0]), 3)
    output_image_path = os.path.join(directory, basename + ".jpg")
    torchvision.utils.save_image(assembled_images.data / 2.0 + 0.5, output_image_path)
    print(weight_path + ' --> ' + output_image_path)

  return 0


if __name__ == '__main__':
  main(sys.argv)