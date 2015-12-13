# Written by Santhosh Kumar Rajendran
#
# Written for Operating Systems Assignment
# by Professor Katz
#
# Specifications :
#
# DONE :
# 1) The DeviceID is correct
# 2) All times are in the past, nothing in the future
# 4) Each directory contains . and .. and their block numbers are correct
# 5) Each directory's link count matches the number of links in the filename_to_inode_dict
# 6) If the data contained in a location pointer is an array, that indirect is one
# 7) That the size is valid for the number of block pointers in the location array. The three possibilities are:
#   a. size<blocksize if  indirect=0 and size>0
#   b. size<blocksize*length of location array if indirect!=0
#   c. size>blocksize*(length of location array-1) if indirect !=0
# 3) Validate that the free block list is accurate this includes
#   a. Making sure the free block list contains ALL of the free blocks
#   b. Make sure than there are no files/directories stored on items listed in the free block list
#
# TO BE DONE :
#

import time

TIME = int(time.time())
FILE_PREFIX = "fusedata."
#FILE_PREFIX = "~/fusedata."
FTID = "filename_to_inode_dict"
BLOCK_SIZE = 4096
OCCUPIED_LIST = []


def gen_file_name(num):
    ''' Generates the file name '''
    file_name = FILE_PREFIX+str(num)
    return file_name


def read_super_block():
    ''' Read the super-block and return it '''

    super_block = {}

    try:
        open_file = open(FILE_PREFIX+"0")
    except IOError:
        print "SuperBlock not found !! Exiting now.. "
        return

    super_block_data = open_file.read().split(',')
    open_file.close()

    (string, value) = super_block_data[0].lstrip('{').split(':')
    super_block[string] = int(value)
    for i in range(1, len(super_block_data)-1):
        (string, value) = super_block_data[i].split(':')
        super_block[string.lstrip(' ')] = int(value)
    (string, value) = super_block_data[len(super_block_data)-1].rstrip('}').split(':')
    super_block[string.lstrip(' ')] = int(value)

    return super_block


def calc_free_blocks(occupied_blocks):
    ''' Calculate the free block list given the occupied list '''
    free_list = range(26, 10000)
    for x in occupied_blocks:
        free_list.remove(x)

    return free_list


def conv_list_to_str(temp_list):
    ''' Convert a list into a continuous string and return it '''
    output_str = ""
    for x in temp_list:
        output_str += str(x)+" "

    return output_str


def check_free_block_list(occ_list):
    ''' Check if the list  '''

    print "Writing actual free blocks onto the files.."

    actual_free_list = calc_free_blocks(occ_list)

    for i in range(1, 26):
        temp_list = []
        for x in actual_free_list:
            if 400*(i-1) <= x < 400*i:
                temp_list.append(x)

        f = open(FILE_PREFIX+str(i), 'w')
        f.write(conv_list_to_str(temp_list))
        f.close()

    print("\n---------------------------------------------------------------------------\n")

    return


def read_dic_node(num):
    ''' Read Folder Node and return it '''
    node = {}

    try:
        open_file = open(FILE_PREFIX+str(num))
    except IOError:
        print "Node not found !! Exiting now.. "
        return

    node_data = open_file.read().split(',')
    open_file.close()

    (string, value) = node_data[0].lstrip('{').split(':')
    node[string] = int(value)
    for i in range(1, 8):
        (string, value) = node_data[i].lstrip('{').split(':')
        node[string.lstrip(' ')] = int(value)

    node[FTID] = {}

    part_data = node_data[8].split(':')
    node[FTID][part_data[-2]] = [part_data[-3].lstrip(" {"), int(part_data[-1])]
    for i in range(9, len(node_data)-1):
        part_data = node_data[i].split(':')
        node[FTID][part_data[-2]] = [part_data[-3].lstrip(" {"), int(part_data[-1])]
    part_data = node_data[len(node_data)-1].split(':')
    node[FTID][part_data[-2]] = [part_data[-3].lstrip(" {"), int(part_data[-1].rstrip("}}"))]

    return node


def read_file_inode(num):
    ''' Read File Inode and return it '''
    node = {}

    try:
        open_file = open(FILE_PREFIX+str(num))
    except IOError:
        print "Node not found !! Exiting now.. "
        return

    node_data = open_file.read().split(',')
    open_file.close()

    (string, value) = node_data[0].lstrip('{').split(':')
    node[string] = int(value)
    for i in range(1, 8):
        (string, value) = node_data[i].lstrip(' ').split(':')
        node[string] = int(value)

    part_node_data = node_data[8].split(' ')

    (string, value) = part_node_data[-2].split(':')
    node[string] = int(value)
    (string, value) = part_node_data[-1].split(':')
    node[string] = int(value.rstrip('}'))

    return node


def nav_fs_by_recursion(node, parent_node_num, current_node_num):
    ''' Recursive method to navigate through the filesystem '''

    check_directory(node, parent_node_num, current_node_num)

    if len(node[FTID]) == 2:
        return

    for stuff in node[FTID]:
        if node[FTID][stuff][0] == 'd' and stuff not in ['..', '.']:
            temp_node = read_dic_node(node[FTID][stuff][1])
            nav_fs_by_recursion(temp_node, current_node_num, node[FTID][stuff][1])

        elif node[FTID][stuff][0] == 'f':
            OCCUPIED_LIST.append(node[FTID][stuff][1])
            temp_node = read_file_inode(node[FTID][stuff][1])
            check_file(temp_node, node[FTID][stuff][1])

    return


def conv_node_proper(dir_inode):
    '''Converts the dir_inode dict into the proper string'''
    inode_dict_string = '{'
    for x in dir_inode['filename_to_inode_dict']:
        inode_dict_string += dir_inode['filename_to_inode_dict'][x][0]+':'+x+':'+str(dir_inode['filename_to_inode_dict'][x][1])+', '
    inode_dict_string = inode_dict_string.rstrip(', ')
    inode_dict_string += '}'

    out_string = "{size:"+str(dir_inode['size'])+", uid:"+str(dir_inode['uid'])+", gid:"+str(dir_inode['gid'])+", mode:"+str(dir_inode['mode'])+", atime:"+str(dir_inode['atime'])+", ctime:"+str(dir_inode['ctime'])+", mtime:"+str(dir_inode['mtime'])+", linkcount:"+str(dir_inode['linkcount'])+", filename_to_inode_dict: "+inode_dict_string+"}"
    return out_string


def conv_file_inode_proper(file_inode):
    ''' Converts the file_inode dict into a string '''
    out_string = "{size:"+str(file_inode['size'])+", uid:"+str(file_inode['uid'])+", gid:"+str(file_inode['gid'])+", mode:"+str(file_inode['mode'])+", linkcount:"+str(file_inode['linkcount'])+", atime:"+str(file_inode['atime'])+", ctime:"+str(file_inode['ctime'])+", mtime:"+str(file_inode['mtime'])+", indirect:"+str(file_inode['indirect'])+" location:"+str(file_inode['location'])+"}"
    return out_string


def check_directory(node, parent_node_num, current_node_num):
    '''Check the folder_inode'''

    print "Performing check on dir : "+str(current_node_num)+".. Parent dir "+str(parent_node_num)

    # Checking the time of access, modification and creation
    if node["atime"] < TIME:
        print "Access time is good !"
    else:
        print "Access time is in the future. Setting it to the current time. "
        node["atime"] = TIME
    if node["ctime"] < TIME:
        print "Creation time is good !"
    else:
        print "Creation time is in the future. Setting it to the current time. "
        node["ctime"] = TIME
    if node["mtime"] < TIME:
        print "Modified time is good !"
    else:
        print "Modified time is in the future. Setting it to the current time. "
        node["mtime"] = TIME

    # Check if . and .. are present
    if '.' not in node['filename_to_inode_dict']:
        print ". not found. Adding it to the folder inode.."
        node['filename_to_inode_dict']['.'] = ['d', current_node_num]
    elif '..' not in node['filename_to_inode_dict']:
        print ".. not found. Adding it to the folder inode.."
        node['filename_to_inode_dict']['..'] = ['d', parent_node_num]

    # Check the link count in the folder
    if len(node['filename_to_inode_dict']) == node['linkcount']:
        print "Link count is good !"
    else:
        print "Link count is incorrect.. Fixing it.."
        node['linkcount'] = len(node['filename_to_inode_dict'])

    # Check the value of current and parent directory
    if node['filename_to_inode_dict']['.'][1] == current_node_num:
        print "Current node is good !"
    else:
        print "Current node is incorrect.. Fixing it.."
        node['filename_to_inode_dict']['.'][1] = current_node_num

    if node['filename_to_inode_dict']['..'][1] == parent_node_num:
        print "Parent node is good !"
    else:
        print "Parent node is incorrect.. Fixing it.."
        node['filename_to_inode_dict']['..'][1] = parent_node_num

    OCCUPIED_LIST.append(node['filename_to_inode_dict']['.'][1])

    print "Writing the fixed details to the directory inode.."
    f = open(FILE_PREFIX+str(current_node_num), 'w')
    f.write(conv_node_proper(node))
    f.close()

    print "\n---------------------------------------------------------------------------\n"

    return


def check_if_array(content):
    ''' Check if the file location is an array of pointers '''

    content_data = content.split()
    for data in content_data:
        if not data.isdigit():
            return False
        elif not 25 < int(data) < 10000:
            return False
    return True


def get_array_from_indirect(content):
    '''Get the indirect inode contents'''
    content_data = content.split()
    return content_data


def get_direct_file_content(file_num):
    ''' Get direct file contents '''
    f = open(FILE_PREFIX+str(file_num))
    contents = f.read()
    return contents


def get_indirect_file_contents(indirect_file_name):
    ''' Get indirect file contents '''
    f = open(FILE_PREFIX+str(indirect_file_name))
    pointers = f.read().split()
    f.close()

    contents = ""
    for x in pointers:
        f = open(FILE_PREFIX+str(x))
        contents += f.read()
        f.close()

    return contents


def check_file(file_inode, file_inode_num):
    ''' Check the file inode and data '''

    print "Performing check on file at : "+str(file_inode_num)

    # Checking if the time of access, creation and modification are in the past
    if file_inode["atime"] < TIME:
        print "Access time is good !"
    else:
        print "Access time is in the future. Setting it to the current time. "
        file_inode["atime"] = TIME
    if file_inode["ctime"] < TIME:
        print "Creation time is good !"
    else:
        print "Creation time is in the future. Setting it to the current time. "
        file_inode["ctime"] = TIME
    if file_inode["mtime"] < TIME:
        print "Modified time is good !"
    else:
        print "Modified time is in the future. Setting it to the current time. "
        file_inode["mtime"] = TIME

    # Check if the data at the location is a list of pointers, if so check if indirect is 1
    f = open(FILE_PREFIX+str(file_inode['location']))
    file_location_content = f.read()
    file_pointers = get_array_from_indirect(file_location_content)
    if check_if_array(file_location_content):
        print "The location of this file is an array of pointers.. Checking if indirect is 1.. "
        if file_inode['indirect'] == 1:
            print "indirect is set to 1. Good !"
        else:
            print "indirect not set to 1. Fixing it.."
            file_inode['indirect'] = 1
    else:
        print "The content is not an array.. Check if indirect is 0.. "
        if file_inode['indirect'] == 0:
            print "indirect is set to 0. Good !"
        else:
            print "indirect not set to 0. Fixing it.."
            file_inode['indirect'] = 0
    f.close()

    # Check if the indirect file has only one pointer. If so fix it..
    if len(file_pointers) == 1:
        print "Only one pointer in the indirect file pointer.. Fixing it.."
        # add the indirect file to the FreeBlocks
        file_inode['indirect'] = 0
        file_inode['location'] = int(file_pointers[0])

    # Check if the file size is right
    if file_inode['indirect'] == 0:
        if file_inode['size'] < BLOCK_SIZE:
            print "Indirect is 0 and File size less than block size. All good !"
        else:
            print "Indirect is 0 and File size is not less than block size.. Fixing the size !!! "
            file_inode['size'] = len(get_direct_file_content(file_inode['location']))
    else:
        if (len(file_pointers)-1)*BLOCK_SIZE < file_inode['size'] < len(file_pointers)*BLOCK_SIZE:
            print "Size of the file in the right range.. All good !"
        else:
            print "Size mismatch.. Fixing the size !!"
            file_inode['size'] = len(get_indirect_file_contents(file_inode['location']))

    if file_inode['indirect'] == 0:
        OCCUPIED_LIST.append(file_inode['location'])
    else:
        f = open(file_inode['location'])
        pointers = f.read().split()
        for x in pointers:
            OCCUPIED_LIST.append(int(x))
        f.close()

    print "Writing the fixed details to file inode.."
    f = open(FILE_PREFIX+str(file_inode_num), 'w')
    f.write(conv_file_inode_proper(file_inode))
    f.close()

    print "\n---------------------------------------------------------------------------\n"

    return


def check_super_block(super_block):
    ''' Check SUPER-BLOCK '''
    print "Checking super block..."

    if super_block["devId"] == 20:
        print "Device ID is good !"
    else:
        print "!!! device ID is wrong !!! Exiting check.."
        exit()

    if super_block["creationTime"] < TIME:
        print "Creation time is good !"
    else:
        print "Creation time is in the future.. Setting it to current time."
        super_block["creationTime"] = TIME

    print "\n---------------------------------------------------------------------------\n"

    return


def main():

    # Reading the superblock
    super_block = read_super_block()

    # Reading the root node
    root_node_num = super_block["root"]
    root_node = read_dic_node(root_node_num)

    # Performing file-system check
    print "\nSTARTING FILE-SYSTEM CHECK.. SIT BACK AND RELAX... \n"

    check_super_block(super_block)

    nav_fs_by_recursion(root_node, root_node_num, root_node_num)

    check_free_block_list(OCCUPIED_LIST)

    return

if __name__ == '__main__':
    main()