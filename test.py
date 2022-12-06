import functions as f
import variables as v

def merge(array, start, mid, end):
  left_subarray = array[start:mid+1]
  right_subarray = array[mid+1:end+1]
  left_head = 0
  right_head = 0
  sorted_head = start
  key_comp = 0

  while left_head < len(left_subarray) and right_head < len(right_subarray):
    left_el = left_subarray[left_head]
    right_el = right_subarray[right_head]
    
    if left_el < right_el:
      left_head += 1
      array[sorted_head] = left_el
    elif left_el == right_el:
      array[sorted_head] = left_el
      sorted_head += 1
      array[sorted_head] = right_el
      left_head += 1
      right_head += 1
    else:
      array[sorted_head] = right_el
      right_head += 1
    
    sorted_head += 1
    key_comp += 1
  
  while left_head < len(left_subarray):
    array[sorted_head] = left_subarray[left_head]
    left_head += 1
    sorted_head += 1
  
  while right_head < len(right_subarray):
    array[sorted_head] = right_subarray[right_head]
    right_head += 1
    sorted_head += 1

  return key_comp
    
def mergeSort(array, start, end):

  key_comp = 0

  if start >= end:
    return 0

  mid = (start + end) // 2
  key_comp += mergeSort(array, start, mid)
  key_comp += mergeSort(array, mid+1, end)
  key_comp += merge(array, start, mid, end)

  return key_comp

S = 5 #placeholder for now

def insertionSort(array, start, end):

  key_comp = 0

  for i in range(start+1, end+1):
    key = array[i]
    j = i - 1

    while j >= start:
      key_comp += 1
      if key < array[j]:
        array[j+1] = array[j]
        j -= 1
      else:
        break

    array[j+1] = key
  
  return key_comp



def hybridSort(array, start, end, S):

  key_comp = 0

  if start >= end:
    return 0

  if end - start <= S:
    key_comp = insertionSort(array, start, end)
  
  else:
    mid = (start + end) // 2
    key_comp += hybridSort(array, start, mid, S)
    key_comp += hybridSort(array, mid+1, end, S)
    key_comp += merge(array, start, mid, end)

  return key_comp

arr_size = []
hybrid_ave_kc = []

for i in range(3,8):
  arr = np.random.randint(1,10**i,10**i).tolist()
  arr_size.append(len(arr))
  hybrid_ave_kc.append(hybridSort(arr,0,len(arr)-1,S))

  print(len(arr), "elements sorted by Hybrid Sort with", hybrid_ave_kc[-1], "key comparisons")

ange_1000 = np.random.randint(1,1000,1000).tolist()
n_fixed_kc = []
S_value = list(range(1,101))


for i in S_value:
  arr = range_1000.copy()
  n_fixed_kc.append(hybridSort(arr,1,len(arr)-1,i))
for i in range(3,8):
  arr = np.random.randint(1,10**i,10**i).tolist()
  arr2 = arr.copy()
  arr_size.append(len(arr))
  hybrid_runtimes.append(timeit.timeit(lambda: hybridSort(arr,0,len(arr)-1,S), number=1))
arr_size=[]
hybrid_runtimes = []

