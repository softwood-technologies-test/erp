import pandas as pd

from django.http import HttpRequest
from django_countries import countries

from .. import models
from .generic_services import askAI, dfToListOfDicts, updateModelWithDF

def GetCustomers(request: HttpRequest, assignFilter: str, countryFilter: str):
    if assignFilter == 'Active':
        customers = models.Customer.objects.filter(AccountManager=request.user)
    else:
        customers = models.Customer.objects.filter(AccountManager = None)

    if countryFilter:
        customers = customers.filter(Country=countryFilter)

    fields = ['id','Name','Country','Website','Address','AccountManager']
    customers = customers.values(*fields)
    if customers:
        dfCustomers = pd.DataFrame(customers)
    else:
        dfCustomers = pd.DataFrame(columns=fields)
    del fields, customers

    dfCustomers = dfCustomers.sample(frac=1)
    dfCustomers = dfCustomers.sort_values(by='Country').reset_index(drop=True)

    data = dfToListOfDicts(dfCustomers)

    listOfCountries = [{'value':None, 'text': 'All Countries'}]
    for code, name in list(countries):
        listOfCountries.append({'value': code, 'text': name})

    return data, listOfCountries

def AddCustomer(dfCustomer: pd.DataFrame, dfCustomerDetails: pd.DataFrame):
    #Raise error if customer name isn't provided
    dfCustomer = dfCustomer[dfCustomer['Name'].str.len()>0]
    if dfCustomer.empty:
        raise ValueError('No Customer provided')    
    
    #Remove rows where customer details aren't provided
    mask = (dfCustomerDetails[dfCustomerDetails.columns].astype(str).apply(lambda row: row.str.len() == 0, axis=1)).all(axis=1)
    dfCustomerDetails = dfCustomerDetails[~mask]

    previousCustomers = models.Customer.objects.all().values('Name','Website')
    customer = dfCustomer.iloc[0].to_dict()

    queryStrings = [
        f"Name: {previousCustomer['Name']} | Website: {previousCustomer['Website']}" for previousCustomer in previousCustomers
    ]
    del previousCustomers

    queryStrings = ", ".join(queryStrings)
    question = f"True or False, is {customer['Name']} in the given list of companies? {queryStrings}?"

    answer = askAI(question)
    del question, queryStrings

    if 'True' in answer:
        raise ValueError('Customer already exists')
    del answer
    
    customer = models.Customer(**customer)
    customer.AccountManager = None
    customer.save()
    
    for _, row in dfCustomerDetails.iterrows():
        if len(row['ContactPersonName']) > 0:
            customerContact = models.CustomerContact(
                Customer = customer,
                Name = row['ContactPersonName'],
                Designation = row['ContactPersonDesignation'],
                IsActive = True
            )
            customerContact.save()

            if (len(row['ContactPersonNumber']) > 0) or (len(row['ContactPersonEmail']) > 0):
                customerContactDetails = models.CustomerContactDetails(
                    Customer = customer,
                    CustomerContact = customerContact,
                    PhoneNumber = row['ContactPersonNumber'],
                    Email = row['ContactPersonEmail']
                )
                customerContactDetails.save()
        else:
            customerContactDetails = models.CustomerContactDetails(
                Customer = customer,
                CustomerContact = None,
                PhoneNumber = row['ContactPersonNumber'],
                Email = row['ContactPersonEmail']
            )
            customerContactDetails.save()
    return customer.id

def GetDataForCustomer (customer: models.Customer):
    customerData = {
        'Name': customer.Name,
        'Website': customer.Website,
        'Address': customer.Address,
        'Country': customer.Country,
        'AccountManager': customer.AccountManager.username if customer.AccountManager else None,
    }

    fields = ['id','Name','Designation','IsActive']
    customerContacts = models.CustomerContact.objects.filter(Customer=customer).values(*fields)
    if customerContacts:
        dfCustomerContacts = pd.DataFrame(customerContacts)
    else:
        dfCustomerContacts = pd.DataFrame(columns=fields)
    del fields, customerContacts
    
    fields = ['id','CustomerContact','PhoneNumber','Email']
    customerContactDetails = models.CustomerContactDetails.objects.filter(Customer=customer).values(*fields)
    if customerContactDetails:
        dfCustomerContactDetails = pd.DataFrame(customerContactDetails)
    else:
        dfCustomerContactDetails = pd.DataFrame(columns=fields)
    del fields, customerContactDetails

    dfCustomerContacts = pd.merge(left=dfCustomerContacts, right=dfCustomerContactDetails, left_on='id', right_on='CustomerContact', how='outer')
    del dfCustomerContactDetails
    dfCustomerContacts.drop(inplace=True, columns=['CustomerContact'])
    dfCustomerContacts.rename(inplace=True, columns={'id_x': 'ContactsId', 'id_y': 'ContactDetailsId'})

    return customerData, dfToListOfDicts(dfCustomerContacts)

def EditCustomer(customer: models.Customer, dfCustomer: pd.DataFrame, dfCustomerDetails: pd.DataFrame):
    customerData = dfToListOfDicts(dfCustomer)[0]
    del dfCustomer
    if len(customerData['Name']) < 1:
        raise ValueError('Customer Name is mandatory')
    
    #Remove rows where customer details aren't provided
    mask = (dfCustomerDetails[dfCustomerDetails.columns.to_list()[:-1]].astype(str).apply(lambda row: row.str.len() == 0, axis=1)).all(axis=1)
    dfCustomerDetails = dfCustomerDetails[~mask]

    for field, value in customerData.items():
        setattr(customer, field, value)
    del customerData
    #customer.save()

    fields = ['id']
    previousContact = models.CustomerContact.objects.filter(Customer=customer).values(*fields)
    if previousContact:
        dfPreiviousContacts = pd.DataFrame(previousContact)
    else:
        dfPreiviousContacts = pd.DataFrame(columns=fields)
    del fields, previousContact

    fields = ['id', 'Customer']
    previousContactDetails = models.CustomerContactDetails.objects.filter(Customer=customer).values(*fields)
    if previousContactDetails:
        dfPreviousContactDetails = pd.DataFrame(previousContactDetails)
    else:
        dfPreviousContactDetails = pd.DataFrame(columns=fields)
    del fields, previousContactDetails

    dfContactPersons = dfCustomerDetails[['ContactsId','ContactPersonName','ContactPersonDesignation','IsActive']]
    dfContactDetails = dfCustomerDetails[['ContactsId','ContactDetailsId','ContactPersonNumber','ContactPersonEmail']]
    del dfCustomerDetails

    for _, row in dfContactDetails.iterrows():
        print(row)