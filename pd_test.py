import pandas as pd

fake_data = [[1, 2, 3], 
            [2, 3, 4], 
            [3, 4, 5]]
fake_data2 = [[1, 4, 5], 
            [2, 6, 7], 
            [3, 8, 9]]
fake_data_name = ['Hz', 'R', 'I']
fake_xyz1 = [1, 2, 3]
fake_xyz2 = [2, 3, 4]

if __name__ == "__main__": 
    pdData = pd.DataFrame(data=fake_data, columns=fake_data_name)
    pdData['x'] = fake_xyz1[0]
    pdData['y'] = fake_xyz1[1]
    pdData['z'] = fake_xyz1[2]
    print(pdData)
    pdData2 = pd.DataFrame(data=fake_data2, columns=fake_data_name)
    pdData2['x'] = fake_xyz2[0]
    pdData2['y'] = fake_xyz2[1]
    pdData2['z'] = fake_xyz2[2]
    print(pdData2)
    print(pdData.append(pdData2)[['x', 'y', 'z', 'Hz', 'R', 'I']].reset_index(drop=True))
