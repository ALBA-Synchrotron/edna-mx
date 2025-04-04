import matplotlib.pyplot as plt
import os
import re
import traceback

def create_quality_indicator_plot(file_stats, out_dir):
    '''
    Creates the I/sigma vs resolution plot, saves to the out_dir, 
    and returns the full path of the generated image
    '''

    image_path = os.path.join(out_dir, "isigma_vs_resolution.png")
    try:
        print("image_path: " + str(image_path))
        
        (x1,x2,y) = parse_unique_stats(file_stats)
        x_resolution = x2
        y_isigma = y
        #x_resolution = x1[1:]
        #y_isigma = y[1:]
        
        print("x_resolution: " + str(x_resolution))
        print("y_isigma: " + str(y_isigma))
        
        plt.ioff()
        #fig, ax = plt.subplots(1, 1)
        fig, ax = plt.subplots()
        plt.xlabel('Resolution')
        plt.ylabel('I/Sigma')
        plt.title('I/Sigma vs Resolution')
        
        ax.xaxis.set_ticks(range(len(x_resolution)))
        ax.xaxis.set_ticklabels(x_resolution)
        
        plt.locator_params(axis='x', nbins=len(x_resolution)/2)
        
        plt.xticks(rotation = 45)
        plt.grid()
        
        plt.plot(list(range(0, len(x_resolution))), y_isigma, marker = 'x')
        plt.savefig(image_path, bbox_inches='tight')
    except Exception:
        ex_message = traceback.print_exc()
        print(f"ERROR with matplotlib.pyplot: {ex_message}")

        
    return image_path



def parse_unique_stats(file_stats):
    '''
    Parses the ..-unique.stats file generated by autoproc to extract the resolution (x1,x2) and the I/Sigma value
    Returns it as a tuple (x1, x2, y)
    '''
    file = open(file_stats, 'r')
    lines = file.readlines()

    header = "Resolution      #uniq     #Rfac  Rmerge   Rmeas    Rpim   #Isig  I/sigI     all     ano    all    ano CC(1/2)  #CCAno CC(ano)  SigAno"
    header_found = False

    x1 = []
    x2 = []
    y = []
    for line in lines:
        line = line.strip()
        if line == header:
            header_found = True

        if header_found:
            
            #self.screen(line)
            result = re.search(r"^(-?\d+\.\d+)[ -]+(-?\d+\.\d+)[ ]+-?\d+[ ]+-?\d+[ ]+-?\d+\.\d+[ ]+-?\d+\.\d+[ ]+-?\d+\.\d+[ ]+-?\d+[ ]+(-?\d+\.\d+)[ ]+-?\d+\.\d+[ ]+-?\d+\.\d+[ ]+-?\d+\.\d+[ ]+-?\d+\.\d+[ ]+-?\d+\.\d+[ ]+-?\d+[ ]+-?\d+\.\d+[ ]+-?\d+\.\d+$", line)
            if result is not None:
                x1.append(float(result.group(1)))
                x2.append(float(result.group(2)))
                y.append(float(result.group(3)))
                # self.screen(result.group(1) + " - " + result.group(2) + ": " + result.group(3))

    file.close()
    if not header_found:
        print(f'ERROR: Expected header {header} nof found in {file_stats}')
    
    return (x1, x2, y)
