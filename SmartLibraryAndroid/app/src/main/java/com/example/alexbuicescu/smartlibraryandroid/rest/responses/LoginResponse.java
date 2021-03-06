package com.example.alexbuicescu.smartlibraryandroid.rest.responses;

import com.google.gson.annotations.SerializedName;

/**
 * Created by alexbuicescu on Oct 22 - 2016.
 */
public class LoginResponse {
    @SerializedName("token")
    private String token;

    @SerializedName("username")
    private String username;

    @SerializedName("user_id")
    private long userId;

    public String getToken() {
        return token;
    }

    public void setToken(String token) {
        this.token = token;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public long getUserId() {
        return userId;
    }

    public void setUserId(long userId) {
        this.userId = userId;
    }
}
