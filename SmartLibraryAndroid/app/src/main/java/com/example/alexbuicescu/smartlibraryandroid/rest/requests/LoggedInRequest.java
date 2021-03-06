package com.example.alexbuicescu.smartlibraryandroid.rest.requests;

import com.google.gson.annotations.SerializedName;

/**
 * Created by alexbuicescu on Oct 22 - 2016.
 */
public class LoggedInRequest {
    @SerializedName("token")
    private String token;

    public LoggedInRequest(String token) {
        this.token = token;
    }

    public String getToken() {
        return token;
    }

    public void setToken(String token) {
        this.token = token;
    }
}
