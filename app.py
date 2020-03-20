# Modified version for Western New York
# Contact: ganaya@buffalo.edu

from functools import reduce
from typing import Tuple, Dict, Any
import pandas as pd
import streamlit as st
import numpy as np
import matplotlib
from bs4 import BeautifulSoup
import requests
import ipyvuetify as v
from traitlets import Unicode, List
import datetime
from datetime import date
import time
import altair as alt

matplotlib.use("Agg")
import matplotlib.pyplot as plt

hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

# General Variables
today = date.today()
fdate = date.today().strftime("%m-%d-%Y")
time = time.strftime("%H:%M:%S")

### Extract data for US
# URL
# 1 Request URL
url = 'https://www.cdc.gov/coronavirus/2019-ncov/cases-updates/cases-in-us.html'
page = requests.get(url)
# 2 Parse HTML content
soup = BeautifulSoup(page.text, 'html.parser')
# 3 Extract cases data
cdc_data = soup.find_all(attrs={"class": "card-body bg-white"})
# Create dataset of extracted data
df = []
for ul in cdc_data:
    for li in ul.find_all('li'):
        df.append(li.text.replace('\n', ' ').strip())
### US specific cases - CDC
cases_us = df[0].split(': ')
# Replace + and , for numeric values
cases_us = int(cases_us[1].replace(',', ''))
# Total US deaths - CDC
deaths_us = df[1].split(': ')
deaths_us = pd.to_numeric(deaths_us[1])
# Calculate mortality rate
us_MR = round((deaths_us/cases_us)*100,2)
# Create table
data = {'Cases': [cases_us],
       'Deaths': [deaths_us],
       'Calculated Mortality Rate': [us_MR]}
us_data = pd.DataFrame(data)

# Extract data for NY State cases
# URL
# 1 Request URL
url = 'https://coronavirus.health.ny.gov/county-county-breakdown-positive-cases'
page = requests.get(url)
# 2 Parse HTML content
soup = BeautifulSoup(page.text, 'html.parser')
# 3 Get the table having the class country table
table = soup.find("div", attrs={'class':"wysiwyg--field-webny-wysiwyg-body"})
table_data = table.find_all("td")
# Get all the headings of Lists
df = []
for i in range(0,len(table_data)):
    for td in table_data[i]:
        df.append(table_data[i].text.replace('\n', ' ').strip())
        


counties = pd.DataFrame([])
for i in range(0, len(df), 2):
    counties = counties.append(pd.DataFrame({'County': df[i], 'Cases': df[i+1]},
                                              index =[0]), ignore_index=True)

    
# NY state Modification for Counties and State Tables
NYC = counties[counties['County']=='New York City'].reset_index()
NYS = counties[counties['County']=='Total Number of Positive Cases'].reset_index()
erie = counties[counties['County']=='Erie'].reset_index()
counties_cases = counties[~(counties['County']=='New York City') & ~(counties['County']=='Total Number of Positive Cases')]
# Remove comma
NYC['Cases'] = pd.to_numeric(NYC['Cases'].str.replace(',', ''))
NYS['Cases'] = pd.to_numeric(NYS['Cases'].str.replace(',', ''))
# Extract value
cases_nys = NYC.Cases[0]
cases_nyc = NYS.Cases[0]
cases_erie = pd.to_numeric(erie.Cases[0])

# Create table
data = {'County': ['Erie', 'New York City', 'New York State'],
       'Cases': [cases_erie, cases_nyc, cases_nys]}
ny_data = pd.DataFrame(data)


# Populations and Infections
buffalo = 258612
tonawanda = 14904
cheektowaga = 87018
amherst = 126082
erie = 1500000
#S_default = erie
known_infections = 20
known_cases = 2
initial_infections = 20

# Widgets
#initial_infections = st.sidebar.number_input(
#    "Currently Known Regional Infections", value=known_infections, step=10, format="%i"
#)

hosp_options = st.sidebar.radio(
    "Hospitals", ('Regional', 'BGH', 'ECMC', 'Mercy', 'MFSH', 'SCH', 'SCSJH'))
    
if hosp_options == 'Regional':
    regional_hosp_share = 1.0
    S = erie * regional_hosp_share
if hosp_options == 'BGH':
    regional_hosp_share = 0.23
    S = erie * regional_hosp_share
if hosp_options == 'ECMC':
    regional_hosp_share = 0.27
    S = erie * regional_hosp_share
if hosp_options == 'Mercy':
    regional_hosp_share = 0.18
    S = erie * regional_hosp_share
if hosp_options == 'MFSH':
    regional_hosp_share = 0.12
    S = erie * regional_hosp_share
if hosp_options == 'SCH':
    regional_hosp_share = 0.15
    S = erie * regional_hosp_share
if hosp_options == 'SCSJH':
    regional_hosp_share = 0.05
    S = erie * regional_hosp_share

current_hosp = st.sidebar.number_input(
    "Currently Hospitalized COVID-19 Patients", value=known_cases, step=1, format="%i"
)

doubling_time = st.sidebar.number_input(
    "Doubling Time (days)", value=6, step=1, format="%i"
)

relative_contact_rate = st.sidebar.number_input(
    "Social distancing (% reduction in social contact)", 0, 100, value=0, step=5, format="%i"
)/100.0

hosp_rate = (
    st.sidebar.number_input("Hospitalization %", 0, 100, value=8, step=1, format="%i")
    / 100.0
)

icu_rate = (
    st.sidebar.number_input("ICU %", 0, 100, value=2, step=1, format="%i") / 100.0
)

vent_rate = (
    st.sidebar.number_input("Ventilated %", 0, 100, value=1, step=1, format="%i")
    / 100.0
)

hosp_los = st.sidebar.number_input("Hospital Length of Stay", value=12, step=1, format="%i")
icu_los = st.sidebar.number_input("ICU Length of Stay", value=9, step=1, format="%i")
vent_los = st.sidebar.number_input("Ventilator Length of Stay", value=7, step=1, format="%i")

#regional_hosp_share = (
#    st.sidebar.number_input(
#        "Hospital Bed Share (%)", 0.0, 100.0, value=100.0, step=1.0, format="%f")
#    / 100.0
#)

#S = st.sidebar.number_input(
#    "Regional Population", value=S_default, step=100000, format="%i"
#)

initial_infections = st.sidebar.number_input(
    "Currently Known Regional Infections (only used to compute detection rate - does not change projections)", value=known_infections, step=10, format="%i"
)
    

total_infections = current_hosp / regional_hosp_share / hosp_rate
detection_prob = initial_infections / total_infections

S, I, R = S, initial_infections / detection_prob, 0

intrinsic_growth_rate = 2 ** (1 / doubling_time) - 1

recovery_days = 14.0
# mean recovery rate, gamma, (in 1/days).
gamma = 1 / recovery_days

# Contact rate, beta
beta = (
    intrinsic_growth_rate + gamma
) / S * (1-relative_contact_rate) # {rate based on doubling time} / {initial S}

r_t = beta / gamma * S # r_t is r_0 after distancing
r_naught = r_t / (1-relative_contact_rate)
doubling_time_t = 1/np.log2(beta*S - gamma +1) # doubling time after distancing

st.title("COVID-19 Hospital Impact Model for Epidemics - Modified for Erie County")
st.markdown(
    """*This tool was developed by the [Predictive Healthcare team](http://predictivehealthcare.pennmedicine.org/) at
Penn Medicine. 

All credit goes to the PH team at Penn Medicine. We have adapted the code based on our current regional cases, county population and hospitals.

For questions about this page, contact ganaya@buffalo.edu. 

For question and comments about the model [contact page](http://predictivehealthcare.pennmedicine.org/contact/).""")

st.markdown(
    """The estimated number of currently infected individuals in Erie County or catchment area by hospital is **{total_infections:.0f}**. The **{initial_infections}** 
confirmed cases in the region imply a **{detection_prob:.0%}** rate of detection. This is based on current inputs for 
Hospitalizations (**{current_hosp}**), Hospitalization rate (**{hosp_rate:.0%}**), Region size (**{S}**), 
and a county wide analysis, as well as Hospital bed share (CCU, ICU, MedSurg).

An initial doubling time of **{doubling_time}** days and a recovery time of **{recovery_days}** days imply an $R_0$ of 
**{r_naught:.2f}**.

**Mitigation**: A **{relative_contact_rate:.0%}** reduction in social contact after the onset of the 
outbreak reduces the doubling time to **{doubling_time_t:.1f}** days, implying an effective $R_t$ of **${r_t:.2f}$**.""".format(
        total_infections=total_infections,
        current_hosp=current_hosp,
        hosp_rate=hosp_rate,
        S=S,
        regional_hosp_share=regional_hosp_share,
        initial_infections=initial_infections,
        detection_prob=detection_prob,
        recovery_days=recovery_days,
        r_naught=r_naught,
        doubling_time=doubling_time,
        relative_contact_rate=relative_contact_rate,
        r_t=r_t,
        doubling_time_t=doubling_time_t
    )
)

st.subheader("Cases of COVID-19 in the United States")
# Table of cases in the US
st.table(us_data)
# Table of cases in NYS
#st.subheader("Cases of COVID-19 in New York State")
#counties.sort_values(by=['Cases'], ascending=False)
#st.table(ny_data)
#st.subheader("Cases of COVID-19 in Erie County")
#st.markdown(
#    """Erie county has reported **{cases_erie:.0f}** cases of COVID-19.""".format(
#        cases_erie=cases_erie
#    )
#)
#st.markdown(""" """)
#st.markdown(""" """)
#st.markdown(""" """)

#fig = go.Figure(data=[go.Table(header=dict(values=['Total Cases', 'Total Deaths', 'Mortality Rate %']),
#                 cells=dict(values=[cases_us, deaths_us, us_MR]))
#                     ])
#st.plotly_chart(fig)


if st.checkbox("Show more info about this tool"):
    st.subheader(
        "[Discrete-time SIR modeling](https://mathworld.wolfram.com/SIRModel.html) of infections/recovery"
    )
    st.markdown(
        """The model consists of individuals who are either _Susceptible_ ($S$), _Infected_ ($I$), or _Recovered_ ($R$).
The epidemic proceeds via a growth and decline process. This is the core model of infectious disease spread and has been in use in epidemiology for many years."""
    )
    st.markdown("""The dynamics are given by the following 3 equations.""")

    st.latex("S_{t+1} = (-\\beta S_t I_t) + S_t")
    st.latex("I_{t+1} = (\\beta S_t I_t - \\gamma I_t) + I_t")
    st.latex("R_{t+1} = (\\gamma I_t) + R_t")

    st.markdown(
        """To project the expected impact to Erie County Hospitals, we estimate the terms of the model.
To do this, we use a combination of estimates from other locations, informed estimates based on logical reasoning, and best guesses from the American Hospital Association.
### Parameters
The model's parameters, $\\beta$ and $\\gamma$, determine the virulence of the epidemic.
$$\\beta$$ can be interpreted as the _effective contact rate_:
""")
    st.latex("\\beta = \\tau \\times c")

    st.markdown(
"""which is the transmissibility ($\\tau$) multiplied by the average number of people exposed ($$c$$).  The transmissibility is the basic virulence of the pathogen.  The number of people exposed $c$ is the parameter that can be changed through social distancing.
$\\gamma$ is the inverse of the mean recovery time, in days.  I.e.: if $\\gamma = 1/{recovery_days}$, then the average infection will clear in {recovery_days} days.
An important descriptive parameter is the _basic reproduction number_, or $R_0$.  This represents the average number of people who will be infected by any given infected person.  When $R_0$ is greater than 1, it means that a disease will grow.  Higher $R_0$'s imply more rapid growth.  It is defined as """.format(recovery_days=int(recovery_days)    , c='c'))
    st.latex("R_0 = \\beta /\\gamma")

    st.markdown("""
$R_0$ gets bigger when
- there are more contacts between people
- when the pathogen is more virulent
- when people have the pathogen for longer periods of time
A doubling time of {doubling_time} days and a recovery time of {recovery_days} days imply an $R_0$ of {r_naught:.2f}.
#### Effect of social distancing
After the beginning of the outbreak, actions to reduce social contact will lower the parameter $c$.  If this happens at 
time $t$, then the number of people infected by any given infected person is $R_t$, which will be lower than $R_0$.  
A {relative_contact_rate:.0%} reduction in social contact would increase the time it takes for the outbreak to double, 
to {doubling_time_t:.2f} days from {doubling_time:.2f} days, with a $R_t$ of {r_t:.2f}.
#### Using the model
We need to express the two parameters $\\beta$ and $\\gamma$ in terms of quantities we can estimate.
- $\\gamma$:  the CDC is recommending 14 days of self-quarantine, we'll use $\\gamma = 1/{recovery_days}$.
- To estimate $$\\beta$$ directly, we'd need to know transmissibility and social contact rates.  since we don't know these things, we can extract it from known _doubling times_.  The AHA says to expect a doubling time $T_d$ of 7-10 days. That means an early-phase rate of growth can be computed by using the doubling time formula:
""".format(doubling_time=doubling_time,
           recovery_days=recovery_days,
           r_naught=r_naught,
           relative_contact_rate=relative_contact_rate,
           doubling_time_t=doubling_time_t,
           r_t=r_t)
    )
    st.latex("g = 2^{1/T_d} - 1")

    st.markdown(
        """
- Since the rate of new infections in the SIR model is $g = \\beta S - \\gamma$, and we've already computed $\\gamma$, $\\beta$ becomes a function of the initial population size of susceptible individuals.
$$\\beta = (g + \\gamma)$$.

### Initial Conditions

- The total size of the susceptible population will be the entire catchment area for Erie County.
- Erie = {erie}
- Buffalo General Hospital with 23% of beds.
- Erie County Medical Center with 27% of beds.
- Mercy Hospital with 18% of beds.
- Millard Fillmore Suburban Hospital with 12% of beds.
- Sisters of Charity Hospital with 15% of beds, and
- Sisters of Charity St. Joeseph Hospital with 5% of beds.""".format(
            erie=erie))


# The SIR model, one time step
def sir(y, beta, gamma, N):
    S, I, R = y
    Sn = (-beta * S * I) + S
    In = (beta * S * I - gamma * I) + I
    Rn = gamma * I + R
    if Sn < 0:
        Sn = 0
    if In < 0:
        In = 0
    if Rn < 0:
        Rn = 0

    scale = N / (Sn + In + Rn)
    return Sn * scale, In * scale, Rn * scale


# Run the SIR model forward in time
def sim_sir(S, I, R, beta, gamma, n_days, beta_decay=None):
    N = S + I + R
    s, i, r = [S], [I], [R]
    for day in range(n_days):
        y = S, I, R
        S, I, R = sir(y, beta, gamma, N)
        if beta_decay:
            beta = beta * (1 - beta_decay)
        s.append(S)
        i.append(I)
        r.append(R)

    s, i, r = np.array(s), np.array(i), np.array(r)
    return s, i, r


n_days = st.slider("Number of days to project", 30, 200, 60, 1, "%i")

beta_decay = 0.0
s, i, r = sim_sir(S, I, R, beta, gamma, n_days, beta_decay=beta_decay)


hosp = i * hosp_rate * regional_hosp_share
icu = i * icu_rate * regional_hosp_share
vent = i * vent_rate * regional_hosp_share

days = np.array(range(0, n_days + 1))
data_list = [days, hosp, icu, vent]
data_dict = dict(zip(["day", "hosp", "icu", "vent"], data_list))

projection = pd.DataFrame.from_dict(data_dict)

st.subheader("New Admissions")
st.markdown("Projected number of **daily** COVID-19 admissions at Erie County or selected Hospital")

# New cases
projection_admits = projection.iloc[:-1, :] - projection.shift(1)
projection_admits[projection_admits < 0] = 0

plot_projection_days = n_days - 10
projection_admits["day"] = range(projection_admits.shape[0])


def new_admissions_chart(projection_admits: pd.DataFrame, plot_projection_days: int) -> alt.Chart:
    """docstring"""
    projection_admits = projection_admits.rename(columns={"hosp": "Hospitalized", "icu": "ICU", "vent": "Ventilated"})
    return (
        alt
        .Chart(projection_admits.head(plot_projection_days))
        .transform_fold(fold=["Hospitalized", "ICU", "Ventilated"])
        .mark_line(point=True)
        .encode(
            x=alt.X("day", title="Days from today"),
            y=alt.Y("value:Q", title="Daily admissions"),
            color="key:N",
            tooltip=["day", "key:N"]
        )
        .interactive()
    )

st.altair_chart(new_admissions_chart(projection_admits, plot_projection_days), use_container_width=True)


if st.checkbox("Show Projected Admissions in tabular form"):
    admits_table = projection_admits[np.mod(projection_admits.index, 7) == 0].copy()
    admits_table["day"] = admits_table.index
    admits_table.index = range(admits_table.shape[0])
    admits_table = admits_table.fillna(0).astype(int)
    
    st.dataframe(admits_table)


st.subheader("Admitted Patients (Census)")
st.markdown(
    "Projected **census** of COVID-19 patients, accounting for arrivals and discharges."
)

# ALOS for each category of COVID-19 case (total guesses)

los_dict = {
    "hosp": hosp_los,
    "icu": icu_los,
    "vent": vent_los,
}

census_dict = dict()
for k, los in los_dict.items():
    census = (
        projection_admits.cumsum().iloc[:-los, :]
        - projection_admits.cumsum().shift(los).fillna(0)
    ).apply(np.ceil)
    census_dict[k] = census[k]


census_df = pd.DataFrame(census_dict)
census_df["day"] = census_df.index
census_df = census_df[["day", "hosp", "icu", "vent"]]

census_table = census_df[np.mod(census_df.index, 7) == 0].copy()
census_table.index = range(census_table.shape[0])
census_table.loc[0, :] = 0
census_table = census_table.dropna().astype(int)

def admitted_patients_chart(census: pd.DataFrame) -> alt.Chart:
    """docstring"""
    census = census.rename(columns={"hosp": "Hospital Census", "icu": "ICU Census", "vent": "Ventilated Census"})

    return (
        alt
        .Chart(census)
        .transform_fold(fold=["Hospital Census", "ICU Census", "Ventilated Census"])
        .mark_line(point=True)
        .encode(
            x=alt.X("day", title="Days from today"),
            y=alt.Y("value:Q", title="Census"),
            color="key:N",
            tooltip=["day", "key:N"]
        )
        .interactive()
    )

st.altair_chart(admitted_patients_chart(census_table), use_container_width=True)

if st.checkbox("Show Projected Census in tabular form"):
    st.dataframe(census_table)

#st.markdown(
#    """**Click the checkbox below to view additional data generated by this simulation**"""
#)

st.subheader(
        "The number of infected and recovered individuals in the region/hospital catchment region at any given moment")

def additional_projections_chart(i: np.ndarray, r: np.ndarray) -> alt.Chart:
    dat = pd.DataFrame({"Infected": i, "Recovered": r})

    return (
        alt
        .Chart(dat.reset_index())
        .transform_fold(fold=["Infected", "Recovered"])
        .mark_line()
        .encode(
            x=alt.X("index", title="Days from today"),
            y=alt.Y("value:Q", title="Case Volume"),
            tooltip=["key:N", "value:Q"], 
            color="key:N"
        )
        .interactive()
    )

st.altair_chart(additional_projections_chart(i, r), use_container_width=True)



if st.checkbox("Show Additional Information"):

    st.subheader("Guidance on Selecting Inputs")
    st.markdown(
        """* **Hospitalized COVID-19 Patients:** The number of patients currently hospitalized with COVID-19. This number is used in conjunction with Hospital Market Share and Hospitalization % to estimate the total number of infected individuals in your region.
        * **Currently Known Regional Infections**: The number of infections reported in your hospital's catchment region. This input is used to estimate the detection rate of infected individuals. 
        * **Doubling Time (days):** This parameter drives the rate of new cases during the early phases of the outbreak. The American Hospital Association currently projects doubling rates between 7 and 10 days. This is the doubling time you expect under status quo conditions. To account for reduced contact and other public health interventions, modify the _Social distancing_ input. 
        * **Social distancing (% reduction in person-to-person physical contact):** This parameter allows users to explore how reduction in interpersonal contact & transmission (hand-washing) might slow the rate of new infections. It is your estimate of how much social contact reduction is being achieved in your region relative to the status quo. While it is unclear how much any given policy might affect social contact (eg. school closures or remote work), this parameter lets you see how projections change with percentage reductions in social contact.
        * **Hospitalization %(total infections):** Percentage of **all** infected cases which will need hospitalization.
        * **ICU %(total infections):** Percentage of **all** infected cases which will need to be treated in an ICU.
        * **Ventilated %(total infections):** Percentage of **all** infected cases which will need mechanical ventilation.
        * **Hospital Length of Stay:** Average number of days of treatment needed for hospitalized COVID-19 patients. 
        * **ICU Length of Stay:** Average number of days of ICU treatment needed for ICU COVID-19 patients.
        * **Vent Length of Stay:**  Average number of days of ventilation needed for ventilated COVID-19 patients.
        * **Hospital Market Share (%):** The proportion of patients in the region that are likely to come to your hospital (as opposed to other hospitals in the region) when they get sick. One way to estimate this is to look at all of the hospitals in your region and add up all of the beds. The number of beds at your hospital divided by the total number of beds in the region times 100 will give you a reasonable starting estimate.
        * **Regional Population:** Total population size of the catchment region of your hospital(s). 
        """)

# Show data
days = np.array(range(0, n_days + 1))
data_list = [days, s, i, r]
data_dict = dict(zip(["day", "susceptible", "infections", "recovered"], data_list))
projection_area = pd.DataFrame.from_dict(data_dict)
infect_table = (projection_area.iloc[::7, :]).apply(np.floor)
infect_table.index = range(infect_table.shape[0])

if st.checkbox("Show Raw SIR Similation Data"):
    st.dataframe(infect_table)







st.subheader("References & Acknowledgements")
st.markdown(
    """
    We appreciate the great work done by Predictive Healthcare team (http://predictivehealthcare.pennmedicine.org/) at
Penn Medicine who created the predictive model used.
    https://www.worldometers.info/coronavirus/coronavirus-incubation-period/
Lauer SA, Grantz KH, Bi Q, et al. The Incubation Period of Coronavirus Disease 2019 (COVID-19) From Publicly Reported Confirmed Cases: Estimation and Application. Ann Intern Med. 2020; [Epub ahead of print 10 March 2020]. doi: https://doi.org/10.7326/M20-0504
http://www.centerforhealthsecurity.org/resources/COVID-19/index.html
http://www.centerforhealthsecurity.org/resources/fact-sheets/pdfs/coronaviruses.pdf'
https://coronavirus.jhu.edu/
https://www.who.int/emergencies/diseases/novel-coronavirus-2019/situation-reports
https://www.worldometers.info/coronavirus/coronavirus-age-sex-demographics/
    """
)
