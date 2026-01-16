from fastapi import FastAPI , Path , HTTPException , Query
from fastapi.responses import JSONResponse
import json
from typing import Annotated, Optional, Literal
from pydantic import BaseModel , Field , computed_field

app=FastAPI()

class Patient(BaseModel):

    id: Annotated[str , Field(..., description='ID of the patient', examples=['P001'])]
    name : Annotated[str , Field(..., description='entre name of the patient')]
    city : Annotated[str , Field(..., description='entre the city of patient')]
    age : Annotated[int , Field(..., gt =0 , lt = 120 , description='age of the patient')]
    gender : Annotated[Literal['Male','Female','others'],Field(..., description='gender of the paient')]
    height : Annotated[float , Field(..., gt = 0 , description='height os the patient in mtrs')]
    weight : Annotated[float , Field(..., gt =0 , description='weight of the patient in kgs')]

    @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight / (self.height**2))
        return bmi
    
    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return 'underweight'
        elif self.bmi < 25:
            return 'normal'
        elif self.bmi < 30:
            return 'normal'
        else:
            return 'obese'
        

class PatientUpdate(BaseModel):
    name : Annotated[Optional[str] , Field(default=None)]
    city : Annotated[Optional[str] , Field(default=None)]
    age : Annotated[Optional[int] , Field(default=None , gt =0)]
    gender : Annotated[Optional[Literal['male','female','other']] , Field(default=None)]
    height : Annotated[Optional[float] , Field(default=None , gt = 0)]
    weight : Annotated[Optional[float] , Field(default=None , gt =0)]


def load_data():
    with open('patients.json','r') as f:
        data=json.load(f)         #this convert data(json) into python dictionary
    return data

def save_data(data):
    with open('patients.json','w') as f:
        json.dump(data , f)    ## converts python object (dict) into json 




@app.get('/')
def hello():
    return {'message' : 'Patient Mangement System API'}

@app.get('/about')
def about():
    return {'message': 'A fully functional API to manage your patient records'}

@app.get('/view')
def patient_record():
    data=load_data()
    return data


@app.get('/patient/{patient_id}')
def view_patient(patient_id: str = Path(..., description='ID of the patient in the db', example='P001')):
    data = load_data()

    if patient_id  in data:
        return data[patient_id]
    raise HTTPException(status_code=404,detail='patient not found')


@app.get('/sort')
def sort_patients(sort_by: str =Query(..., description='sort on the basis of Height , Weight or BMI'), order : str = Query('asc' , description='sort in asc or desc order') ):

    valid_fields = ['height','weight','bmi']

    if sort_by not in  valid_fields:
        raise HTTPException(status_code=400 , detail=f'Invalid field select from {valid_fields}')
    if order not in ['asc' , 'desc']:
        raise HTTPException(status_code=400, detail='Invalid order select between asc ans desc')
    
    data= load_data()

    sort_order=True if order == 'desc' else False

    sorted_data=sorted(data.values(),key = lambda x :x.get(sort_by , 0), reverse = sort_order) ## .get is use to take value from dict using the key here key is sort_by that is height,weight,bmi

    return sorted_data


@app.post('/create')
def create_patient(patient : Patient):        ##data from request body will go to pydantic model for validation then come in patient variable in form pydantic object
    ## load  data
    data = load_data()

    ## check if patient atready exists
    if patient.id in data:
        raise HTTPException(status_code=400 , detail='patient already exists')

    ## new patient add to the database
    data[patient.id]= patient.model_dump(exclude =['id'])

    ## save into the json file
    save_data(data)

    return JSONResponse(status_code=201 , content={'message':'patient created sucessfully'})


@app.put('/edit/{patient_id}')
def update_patient(patient_id : str , patient_update : PatientUpdate):

    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404 , detail='patient not found')
    
    existing_patient_info = data[patient_id]

    updated_patient_info = patient_update.model_dump(exclude_unset=True)  

    for key,value in updated_patient_info.items():
        existing_patient_info[key] = value


    #existing_patient_infoo -> pydantic object -> updated bmi + verdict
    existing_patient_info['id'] = patient_id
    patient_pydantic_object=Patient(**existing_patient_info)
    #pydantic obj to dict
    existing_patient_info=patient_pydantic_object.model_dump(exclude='id')

    ##add this dict to data
    data[patient_id] = existing_patient_info

    #save data
    save_data(data)

    return JSONResponse(status_code=200 , content={'message':'patient updated'})

@app.delete('/delete/{patient_id}')
def delete_patient(patient_id:str):
    data=load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404,detail='patient not found')
    del data[patient_id]
    save_data(data)

    return JSONResponse(status_code=200,content={'message':'patient deleted'})


