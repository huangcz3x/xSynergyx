import './Login.css';
import React from 'react';
import { GoogleLogout } from 'react-google-login';

//might still need to require dotenv. Check again in an hour
//require('dotenv').config()

const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;
console.log(process.env);

function Logout() {
    
    const onSuccess = (res) => {
        alert('Lougout made successfully');
    };
    
    return (
        <div>
            <GoogleLogout
                clientId={clientId}
                buttonText="Logout"
                onLogoutSuccess={onSuccess}
            ></GoogleLogout>
        </div>
        );
}

export default Logout;