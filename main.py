import streamlit as st
import pandas as pd
import gspread

from oauth2client.service_account import ServiceAccountCredentials


def is_date_within_the_last_60_days(row):
    return row.Submitted >= (pd.to_datetime('today') - pd.Timedelta(days=60)).strftime('%Y-%m-%d')

st.set_page_config(page_title='Talkdesk to SimpleTexting', page_icon='⚙️', layout="centered", initial_sidebar_state="auto", menu_items=None)


st.caption('VACAYZEN')
st.title('Talkdesk to SimpleTexting')
st.info('Convert the Prior Day Calls Report from Talkdesk to a contact list file for SimpleTexting.')

file = st.file_uploader('Prior Day Calls Report','CSV')

if file is not None:

    df = pd.read_csv(file, index_col=False)
    df = df[df['Call Type'] == 'inbound']
    df = df[df['Phone Display Name'].isin(st.secrets['display_names'])]
    df = df[['Customer Phone Number']]
    df.columns = ['Phone']
    df = df.drop_duplicates()

    credentials = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets['key'], st.secrets['scope'])
    client      = gspread.authorize(credentials)
    sheet       = client.open(st.secrets['sheet']).worksheet(st.secrets['tab'])
    values      = sheet.get_values(st.secrets['range'])

    af = pd.DataFrame(values, columns=['Phone','Submitted'])
    af['keep'] = af.apply(is_date_within_the_last_60_days, axis=1)
    af = af[af.keep][['Phone']]

    new          = df['Phone'].to_list()
    old          = af['Phone'].to_list()
    add_download = []
    add_upload   = []

    for number in new:
        if not number[1:] in old:
            add_download.append(number)
            add_upload.append(number[1:])

    add_df   = pd.DataFrame({'Phone': add_download})
    combined = old + add_upload
    final    = pd.DataFrame({'Phone': combined})


    if st.download_button('DOWNLOAD CONTACT LIST', add_df.to_csv(index=False), 'SimpleTexting.csv', 'CSV', use_container_width=True, type='primary'):
        final['Submitted'] = pd.to_datetime('today').date()
        final  = final.astype(str)
        update = [final.columns.values.tolist()] + final.values.tolist()

        sheet.update(range_name='A1', values=update)